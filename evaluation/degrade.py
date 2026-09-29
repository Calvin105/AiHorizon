"""Camera-style degradations for the stress test.

There are no real production photos, so instead of claiming the vision
step works on them, this measures how far a clean synthetic image can be
damaged — in the ways a real camera damages one — before the measurement
goes wrong, and whether the quality gate catches it when it does.

Each degradation takes a BGR uint8 image and a severity level; levels run
from "a decent bench camera" to "clearly unusable". The numbers are
chosen as plausible ranges, not calibrated against any specific camera.
"""

from __future__ import annotations

from collections.abc import Callable

import cv2
import numpy as np

Degrade = Callable[[np.ndarray, float, np.random.Generator], np.ndarray]


def _clip(img: np.ndarray) -> np.ndarray:
    return np.clip(img, 0, 255).astype(np.uint8)


def blur(img, sigma, _rng):
    return cv2.GaussianBlur(img, (0, 0), sigmaX=sigma)


def noise(img, sigma, rng):
    return _clip(img.astype(np.float32) + rng.normal(0, sigma, img.shape))


def uneven_light(img, strength, _rng):
    """A linear brightness ramp across the frame — a ring light off to one
    side, or a window. Strength is the grey-level swing edge to edge."""
    w = img.shape[1]
    ramp = np.linspace(-strength / 2, strength / 2, w, dtype=np.float32)
    return _clip(img.astype(np.float32) + ramp[None, :, None])


def glare(img, strength, rng):
    """A soft bright hotspot — specular reflection off a glossy deposit or
    board. Strength is the grey-level peak at its centre."""
    h, w = img.shape[:2]
    cy, cx = rng.uniform(0.25, 0.75) * h, rng.uniform(0.25, 0.75) * w
    yy, xx = np.mgrid[0:h, 0:w]
    spot = strength * np.exp(-(((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * (0.18 * max(h, w)) ** 2)))
    return _clip(img.astype(np.float32) + spot[:, :, None])


def low_contrast(img, factor, _rng):
    """Factor is how much contrast is kept: 1.0 unchanged, 0.2 washed out."""
    f = img.astype(np.float32)
    mean = f.mean()
    return _clip((f - mean) * factor + mean)


def jpeg(img, quality, _rng):
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, int(quality)])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR) if ok else img


def rotate(img, degrees, _rng):
    """The part or camera sitting slightly skewed against the recipe."""
    h, w = img.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), degrees, 1.0)
    return cv2.warpAffine(img, m, (w, h), borderMode=cv2.BORDER_REPLICATE)


def shift(img, pixels, _rng):
    """The part or camera offset from where the recipe expects it."""
    h, w = img.shape[:2]
    m = np.float32([[1, 0, pixels], [0, 1, pixels * 0.5]])
    return cv2.warpAffine(img, m, (w, h), borderMode=cv2.BORDER_REPLICATE)


def low_resolution(img, factor, _rng):
    """The camera too far away: resolve the frame at `factor` of its size,
    then scale back so the recipe's pixel coordinates still apply."""
    h, w = img.shape[:2]
    small = cv2.resize(img, (max(1, int(w * factor)), max(1, int(h * factor))), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)


def board_clutter(img, count, rng):
    """What a real board has behind the deposits and the synthetic canvas
    does not: copper pads, traces and silkscreen, in greys between the
    background and the deposit. Drawn only on background pixels, so the
    deposits themselves are untouched."""
    h, w = img.shape[:2]
    layer = img.copy()
    for _ in range(int(count)):
        grey = int(rng.uniform(120, 200))
        colour = (grey, grey, grey)
        if rng.random() < 0.5:
            x, y = int(rng.uniform(0, w)), int(rng.uniform(0, h))
            cv2.rectangle(layer, (x, y), (x + int(rng.uniform(15, 60)), y + int(rng.uniform(10, 40))), colour, -1)
        else:
            p1 = (int(rng.uniform(0, w)), int(rng.uniform(0, h)))
            p2 = (int(rng.uniform(0, w)), int(rng.uniform(0, h)))
            cv2.line(layer, p1, p2, colour, int(rng.uniform(2, 7)))
    background = img.mean(axis=2) > 180
    out = img.copy()
    out[background] = layer[background]
    return out


def phone_photo(img, level, rng):
    """Several mild faults at once, the way a real handheld photo has them,
    all scaled together by `level` (1 = mild, 4 = bad)."""
    out = blur(img, 0.6 * level, rng)
    out = uneven_light(out, 15 * level, rng)
    out = noise(out, 3 * level, rng)
    return jpeg(out, max(95 - 18 * level, 10), rng)


# name -> (function, severity levels mild -> severe, unit shown in reports)
DEGRADATIONS: dict[str, tuple[Degrade, list[float], str]] = {
    "blur": (blur, [1, 2, 4, 7], "sigma px"),
    "noise": (noise, [8, 16, 32, 56], "sigma grey levels"),
    "uneven_light": (uneven_light, [30, 60, 110, 170], "grey levels edge to edge"),
    "glare": (glare, [40, 80, 130, 180], "peak grey levels"),
    "low_contrast": (low_contrast, [0.6, 0.4, 0.25, 0.12], "contrast kept"),
    "jpeg": (jpeg, [60, 35, 15, 5], "quality"),
    "rotate": (rotate, [1, 2, 4, 8], "degrees"),
    "shift": (shift, [5, 12, 25, 50], "px"),
    "low_resolution": (low_resolution, [0.5, 0.3, 0.2, 0.12], "of full resolution"),
    "board_clutter": (board_clutter, [5, 15, 30, 60], "pads/traces"),
    "phone_photo": (phone_photo, [1, 2, 3, 4], "combined level"),
}
