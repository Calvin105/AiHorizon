"""The public entry point: detect(image_bytes, profile) -> a structured
report of what's wrong and where.
"""

from __future__ import annotations

import math
import statistics

import cv2
import numpy as np

from . import classify as _classify
from .align import align
from .profile import load_profile
from .register import register
from .segment import segment_image

SATURATED_LEVEL = 250
WASHED_OUT_CONTRAST = (0.1, 0.6)
"""A deposit keeping between these shares of the image's typical deposit
contrast, inside clipped surroundings, is being washed out by glare. Below
the band there is no deposit to see -- indistinguishable from a genuinely
missing one, so it is left to be reported as missing. A glare patch is a
smooth falloff, so one strong enough to erase deposits outright always
leaves partly-faded ones around it, and those trip the band."""


def _gray(bgr: np.ndarray) -> np.ndarray:
    """Median-filtered so saturation is judged on regions: isolated white
    pixels (sensor hot pixels, or vision/synth's canvas noise) aren't glare."""
    return cv2.medianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), 5)


def _saturated_fraction(gray: np.ndarray) -> float:
    return round(float(np.count_nonzero(gray >= SATURATED_LEVEL)) / gray.size, 4)


def _disk_median(gray: np.ndarray, cx: float, cy: float, r_in: float, r_out: float) -> float | None:
    h, w = gray.shape
    x0, x1 = max(0, int(cx - r_out)), min(w, int(cx + r_out) + 1)
    y0, y1 = max(0, int(cy - r_out)), min(h, int(cy + r_out) + 1)
    if x0 >= x1 or y0 >= y1:
        return None
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    pixels = gray[y0:y1, x0:x1][(d2 >= r_in**2) & (d2 <= r_out**2)]
    return float(np.median(pixels)) if pixels.size else None


def _washed_out_deposits(gray: np.ndarray, profile) -> int:
    """Recipe positions a glare patch has made unreadable. White background
    alone is harmless -- a dark deposit on it still measures fine. The harm
    is a deposit lifted toward the background, where the threshold starts
    cutting it down to undersized, irregular or missing. So a position
    counts only if its surroundings are clipped AND its own contrast has
    partly collapsed against the image's typical (90th percentile) deposit."""
    samples = []
    for p in profile.points:
        inner = _disk_median(gray, p.cx, p.cy, 0.0, 0.5 * p.r)
        ring = _disk_median(gray, p.cx, p.cy, 1.6 * p.r, 2.2 * p.r)
        if inner is not None and ring is not None:
            samples.append((abs(ring - inner), ring))
    if not samples:
        return 0
    typical = max(float(np.percentile([c for c, _ in samples], 90)), 1.0)
    lo, hi = WASHED_OUT_CONTRAST
    return sum(1 for c, ring in samples if ring >= SATURATED_LEVEL and lo * typical < c < hi * typical)


def detect(raw: bytes, profile_data: dict | None = None) -> dict:
    decoded = segment_image(raw)
    if decoded is None:
        return {"error": "Could not decode that image."}
    bgr, blobs = decoded
    gray = _gray(bgr)
    # Facts about the photo itself, for a downstream quality gate to judge
    # -- this module reports, it doesn't refuse.
    image_quality: dict = {"saturated_fraction": _saturated_fraction(gray)}

    if not profile_data or not profile_data.get("profile"):
        # No known recipe to check against -- alignment-dependent symptoms
        # (missing, misaligned, fused) need a nominal position to compare
        # to, which nothing here should guess. Raw measurements only.
        return {
            "profile_supplied": False,
            "image_quality": image_quality,
            "blob_count": len(blobs),
            "note": "No profile supplied: returning raw per-blob measurements only, no classification.",
            "blobs": [
                {"cx": round(b["cx"], 2), "cy": round(b["cy"], 2),
                 "area": round(b["area"], 1), "circularity": round(b["circularity"], 3)}
                for b in blobs
            ],
        }

    # The recipe in photo coordinates: a photo zoomed, rotated or framed
    # off-centre is lined up first, so every position is judged where it
    # actually landed. A photo already framed like the recipe is untouched.
    profile, registration = register(blobs, load_profile(profile_data))
    matches, extra = align(blobs, profile)
    image_quality["washed_out_deposits"] = _washed_out_deposits(gray, profile)

    dots = [_classify.classify_point(m) for m in matches]
    _classify.classify_array(dots)  # inconsistent volume: an array-level property
    extras = [_classify.classify_extra(b) for b in extra]
    # Size of each stray blob against a nominal deposit, so a consumer can
    # tell a satellite or speck (a few % of a dot) from something dot-sized
    # that isn't on the recipe at all -- a pad, trace or marking.
    nominal_area = statistics.median(math.pi * p.r**2 for p in profile.points) if profile.points else 0.0
    for e in extras:
        e["area_ratio"] = round(e["area"] / nominal_area, 3) if nominal_area else None

    counts: dict[str, int] = {}
    for d in dots + extras:
        for t in d["tags"]:
            counts[t] = counts.get(t, 0) + 1

    flagged = sum(1 for d in dots if d["tags"])
    return {
        "profile_supplied": True,
        "image_quality": image_quality,
        "pattern": profile.pattern,
        # A downstream consumer (dashboard, MES, line-stop signal) usually
        # just needs pass/fail plus a count -- added here so it doesn't have
        # to re-derive that by scanning every dot's tags itself.
        "summary": {
            "status": "fail" if (flagged or extras) else "pass",
            "dot_count": len(dots),
            "flagged_count": flagged,
            "extra_count": len(extras),
        },
        "dots": dots,
        "extra": extras,
        "counts": counts,
        "registration": registration.as_dict(),
        # Where each recipe position was looked for in this photo — what an
        # annotation has to draw against once the photo was registered.
        "positions": [
            {"index": pt.index, "cx": round(pt.cx, 2), "cy": round(pt.cy, 2), "r": round(pt.r, 2)}
            for pt in profile.points
        ],
    }
