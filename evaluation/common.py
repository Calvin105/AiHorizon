"""Shared plumbing: puts the real pipeline on the import path and wraps the
two calls every part of the evaluation makes — build a synthetic photo with
known ground truth, and measure it through the *same* run_vision() the API
calls. Nothing here re-implements pipeline logic; if the app changes, the
evaluation measures the change.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
for path in (ROOT / "vision", ROOT / "pipeline" / "backend"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import cv2
import numpy as np
from synth import dataset

from app.domains.vision.service import VisionResult, run_vision

SPEC_LIMIT = 0.15  # size_cv; the demo profile's spec, and DESIGN.md's worked example
CHANCE_P = 0.05


def make_image(
    pattern: str, defects: list[str], seed: int, params: dict[str, dict] | None = None
) -> tuple[np.ndarray, dict]:
    """A synthetic photo plus the recipe geometry the app would already hold
    for it (the profile, not the ground truth — detect() never sees tags)."""
    rng = np.random.default_rng(seed)
    img, layout, n_profile = dataset.build_image(pattern, defects, rng, defect_params=params)
    sidecar = dataset._sidecar(layout, defects, n_profile)
    geometry = {k: sidecar[k] for k in ("pattern", "width", "height", "profile")}
    return img, geometry


def measure(img: np.ndarray, geometry: dict) -> VisionResult:
    ok, png = cv2.imencode(".png", img)
    if not ok:
        raise RuntimeError("could not encode image")
    return run_vision(png.tobytes(), geometry, SPEC_LIMIT)


def carryover_above_chance(signals: dict) -> bool:
    p = signals.get("small_then_big_chance_p")
    return bool(signals.get("small_then_big_count")) and p is not None and p < CHANCE_P
