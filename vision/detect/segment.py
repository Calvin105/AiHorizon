"""Pure image segmentation: Otsu threshold + external contours -> a blob
list. No dependency on anything else in this repo -- this is the low-level
part of the pipeline most likely to be reused as-is in a real product.

Same method as the original vision/main.py service; factored out here so
there is one implementation instead of two drifting apart.
"""

from __future__ import annotations

import math

import cv2
import numpy as np

MIN_AREA_FRACTION = 5e-4

FLATTEN_MIN_RANGE = 25.0
"""Grey levels of background variation (5th-95th percentile of the
estimated background) before flattening kicks in. Below it the photo is
evenly lit and segment() behaves exactly as it did before flattening
existed -- so the fix for uneven light cannot cost anything on the photos
that were already measuring correctly."""

_BG_DOWNSCALE = 4


def estimate_background(gray: np.ndarray) -> np.ndarray:
    """The frame with the deposits removed: a median over a window several
    deposits wide. Deposits are a minority of any such window, so the
    median lands on background whichever polarity they are. Computed at
    1/4 scale -- lighting varies slowly, and a full-size median this wide
    is needlessly slow."""
    h, w = gray.shape
    small = cv2.resize(gray, (max(1, w // _BG_DOWNSCALE), max(1, h // _BG_DOWNSCALE)), interpolation=cv2.INTER_AREA)
    k = max(3, (min(small.shape) // 2) | 1)  # odd, about half the short side
    bg_small = cv2.medianBlur(small, k)
    return cv2.resize(bg_small, (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32)


def flatten_illumination(gray: np.ndarray) -> tuple[np.ndarray, float]:
    """Subtracts slow lighting variation (a light off to one side, a broad
    glare patch) so one global threshold fits the whole frame again.
    Returns the corrected image and the background range that was found."""
    bg = estimate_background(gray)
    lo, hi = np.percentile(bg, [5, 95])
    bg_range = float(hi - lo)
    if bg_range < FLATTEN_MIN_RANGE:
        return gray, bg_range
    level = float(np.median(bg))
    flat = gray.astype(np.float32) - bg + level
    return np.clip(flat, 0, 255).astype(np.uint8), bg_range


def segment(gray: np.ndarray) -> np.ndarray:
    """Otsu threshold, oriented so deposits are foreground regardless of polarity."""
    gray, _ = flatten_illumination(gray)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    if np.count_nonzero(binary) > binary.size * 0.5:
        binary = cv2.bitwise_not(binary)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    return cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)


def measure_blobs(binary: np.ndarray, frame_area: float) -> list[dict]:
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    blobs = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < frame_area * MIN_AREA_FRACTION:
            continue
        perimeter = cv2.arcLength(c, True)
        if perimeter <= 0:
            continue
        m = cv2.moments(c)
        if m["m00"] == 0:
            continue
        blobs.append(
            {
                "area": float(area),
                "perimeter": float(perimeter),
                "circularity": float(min(1.0, 4 * math.pi * area / (perimeter**2))),
                "cx": float(m["m10"] / m["m00"]),
                "cy": float(m["m01"] / m["m00"]),
                "equivalent_diameter": float(2 * math.sqrt(area / math.pi)),
            }
        )
    return blobs


SUBSTRATE_SHARE = (0.15, 0.92)
"""How much of the frame a part lying on a darker surface plausibly covers."""
SUBSTRATE_EDGE_CONTACT = 0.25
"""At or above this share of the frame's edge pixels on the substrate, the
photo is framed on the part itself and there is no surround to mask."""


def mask_surround(gray: np.ndarray) -> tuple[np.ndarray, float | None]:
    """A part photographed lying on something darker — a card on a desk, a
    board in a fixture — comes back with the surround painted in the
    substrate's own grey, so segment() sees what it was built for: deposits
    on one background. Painted rather than cropped, so every coordinate
    still refers to the original photo.

    Without this, illumination flattening reads the desk-to-card edge as a
    lighting gradient, and the deposits merge into the grey blob it leaves.
    Untouched whenever the light substrate already reaches the frame edge,
    which every photo framed on the part itself does — so no photo the
    pipeline already measured is affected.

    Returns the image and, when a surround was masked, the substrate's area:
    the speck floor in measure_blobs() is a share of the part, not of a photo
    that happens to include a lot of desk."""
    h, w = gray.shape
    blurred = cv2.GaussianBlur(gray, (9, 9), 0)
    _, light = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(light, connectivity=8)
    if count <= 1:
        return gray, None
    biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    share = stats[biggest, cv2.CC_STAT_AREA] / float(h * w)
    if not SUBSTRATE_SHARE[0] <= share <= SUBSTRATE_SHARE[1]:
        return gray, None
    region = labels == biggest
    edge = np.concatenate([region[0], region[-1], region[:, 0], region[:, -1]])
    if edge.mean() >= SUBSTRATE_EDGE_CONTACT:
        return gray, None

    # The substrate's outline, holes (the deposits themselves) filled, pulled
    # in a little so the substrate's own bright rim and shadow go too.
    contours, _ = cv2.findContours(region.astype(np.uint8) * 255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    outline = np.zeros((h, w), np.uint8)
    cv2.drawContours(outline, [max(contours, key=cv2.contourArea)], -1, 255, thickness=cv2.FILLED)
    margin = max(3, int(0.015 * min(h, w))) | 1
    outline = cv2.erode(outline, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (margin, margin)))

    painted = gray.copy()
    painted[outline == 0] = np.uint8(np.median(gray[region]))
    return painted, float(np.count_nonzero(outline))


def segment_image(raw: bytes) -> tuple[np.ndarray, list[dict]] | None:
    """Bytes in, (bgr image, blob list) out. None if the bytes don't decode."""
    arr = np.frombuffer(raw, np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        return None
    gray, substrate_area = mask_surround(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))
    frame_area = substrate_area or float(gray.shape[0] * gray.shape[1])
    binary = segment(gray)
    blobs = measure_blobs(binary, frame_area)
    return bgr, blobs
