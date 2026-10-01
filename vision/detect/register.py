"""Line the recipe up with the photo before matching.

align.py matches each detected blob to the profile position nearest it, in
the profile's own pixel coordinates. That only works when the photo is
framed exactly like the recipe — same resolution, same crop. A phone photo
never is: evaluation/ measured a good board refused 100% of the time once
it was zoomed, moved off-centre, or both.

This finds the similarity transform (scale, rotation, shift) that carries
the recipe onto the photo's deposits, and hands align() the recipe in
photo coordinates. Classical and auditable, like the rest of detect/:

  1. scale candidates from two independent readings — the dot pitch (the
     lower quartile of nearest-neighbour spacing) and the deposit size
     (median deposit area against the recipe's nominal area). Missing dots
     stretch the pitch; a uniform size fault skews the area; they rarely
     both mislead at once.
  2. for each scale and a small grid of rotations, anchor one recipe
     position on one deposit and count how many other positions then land
     on a deposit. Every anchor pairing is tried, so it doesn't matter which
     dots are missing — any one present dot can anchor the fit.
  3. refine the best hypothesis with iterative closest point: pair each
     position with its nearest deposit and refit the transform to those
     pairs (least-median of squares, so a stray blob can't pull it).

Registering is a last resort, not a default. A photo already framed like
the recipe — most positions find a deposit, at the recipe's own spacing —
is measured exactly as before, so a whole pattern dispensed off-position
still reads as misaligned rather than being "corrected" away. Only a photo
that clearly isn't framed like the recipe is registered, and the result is
used only if it reaches clearly more positions than the photo as framed.
On a registered photo an offset shared by every deposit can't be told
apart from framing, and `registration` in detect()'s output says it was
applied.

What this does not undo: a camera tilted enough to foreshorten the
pattern (that needs a homography and fiducials), rotation past
MAX_ROTATION_DEG, or a pattern cropped out of frame (a deposit that isn't
in the picture reads as missing).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

import cv2
import numpy as np

from .profile import Profile, ProfilePoint

CAPTURE_FACTOR = 1.8
"""align.py's own reach: a deposit within 1.8 r of a position is on it."""
SPECK_FRACTION = 0.2
"""Blobs under this share of the median blob area are specks or satellites,
not deposits — left out of the fit, though align() still sees them."""
MIN_PAIRS = 3
FRAMED_SHARE = 0.7
"""Positions finding a deposit, as framed, at or above which the photo is
taken to be framed like the recipe (missing dots allowed for)."""
SCALE_TOLERANCE = 0.1
"""Dot spacing within this fraction of the recipe's is the recipe's scale."""
ACCEPT_SHARE = 0.5
"""A registration has to put a deposit on at least this share of positions..."""
GAIN_SHARE = 0.2
"""...and reach clearly more of them than the photo as framed: this share of
the pattern, and never fewer than two. Winning by one position is what a
fused or smeared deposit pulling the fit sideways looks like."""
MAX_ROTATION_DEG = 15
ROTATION_STEP_DEG = 5
SCALE_NUDGES = (0.92, 1.0, 1.08)
MAX_ANCHORS = 8
"""Recipe positions tried as anchors, spread across the pattern."""
ICP_ROUNDS = 10


@dataclass
class Registration:
    applied: bool
    scale: float = 1.0
    rotation_deg: float = 0.0
    shift_px: tuple[float, float] = (0.0, 0.0)
    positions_matched: int = 0
    """Recipe positions with a deposit within reach, as measured."""
    positions_matched_as_framed: int = 0
    """The same count with the photo taken as framed, before registering."""
    positions: int = 0

    def as_dict(self) -> dict:
        return {
            "applied": self.applied,
            "scale": round(self.scale, 4),
            "rotation_deg": round(self.rotation_deg, 2),
            "shift_px": [round(self.shift_px[0], 1), round(self.shift_px[1], 1)],
            "positions_matched": self.positions_matched,
            "positions_matched_as_framed": self.positions_matched_as_framed,
            "positions": self.positions,
        }


def _pitch(points: np.ndarray) -> float:
    d = np.linalg.norm(points[:, None] - points[None], axis=2)
    np.fill_diagonal(d, np.inf)
    return float(np.percentile(d.min(axis=1), 25))


def _apply(m: np.ndarray, pts: np.ndarray) -> np.ndarray:
    return pts @ m[:, :2].T + m[:, 2]


def _reached(positions: np.ndarray, radii: np.ndarray, blobs: np.ndarray) -> int:
    """Positions with a deposit within align()'s reach."""
    d = np.linalg.norm(positions[:, None] - blobs[None], axis=2).min(axis=1)
    return int(np.sum(d <= radii * CAPTURE_FACTOR))


def _anchors(recipe: np.ndarray) -> np.ndarray:
    """Up to MAX_ANCHORS position indices spread over the pattern — the ones
    nearest evenly spaced points along its longer extent."""
    n = len(recipe)
    if n <= MAX_ANCHORS:
        return np.arange(n)
    axis = int(np.ptp(recipe[:, 1]) > np.ptp(recipe[:, 0]))
    order = np.argsort(recipe[:, axis])
    return order[np.linspace(0, n - 1, MAX_ANCHORS).round().astype(int)]


def _best_hypothesis(
    recipe: np.ndarray, radii: np.ndarray, deposits: np.ndarray, scales: list[float],
) -> np.ndarray | None:
    """The scale/rotation/anchor pairing that lands the most positions on
    deposits, as a 2x3 similarity matrix."""
    anchors = _anchors(recipe)
    best: tuple[int, float, np.ndarray] | None = None
    rotations = np.radians(np.arange(-MAX_ROTATION_DEG, MAX_ROTATION_DEG + 1, ROTATION_STEP_DEG))
    for scale in scales:
        reach = radii * scale * CAPTURE_FACTOR
        for theta in rotations:
            c, s = math.cos(theta), math.sin(theta)
            rot = scale * np.array([[c, -s], [s, c]])
            turned = recipe @ rot.T                                   # (n, 2)
            shifts = deposits[None, :, :] - turned[anchors][:, None, :]  # (a, m, 2)
            placed = turned[None, None] + shifts[:, :, None, :]       # (a, m, n, 2)
            d = np.linalg.norm(placed[:, :, :, None, :] - deposits[None, None, None], axis=4).min(axis=3)
            hits = (d <= reach).sum(axis=2)                           # (a, m)
            spread = np.where(d <= reach, d, 0.0).sum(axis=2)
            a, j = np.unravel_index(np.lexsort((spread.ravel(), -hits.ravel()))[0], hits.shape)
            candidate = (int(hits[a, j]), float(spread[a, j]))
            if best is None or (candidate[0], -candidate[1]) > (best[0], -best[1]):
                m = np.hstack([rot, shifts[a, j][:, None]])
                best = (candidate[0], candidate[1], m)
    return None if best is None else best[2]


def _refine(m: np.ndarray, recipe: np.ndarray, deposits: np.ndarray, pitch: float) -> np.ndarray:
    for _ in range(ICP_ROUNDS):
        scale = math.hypot(m[0, 0], m[1, 0])
        moved = _apply(m, recipe)
        d = np.linalg.norm(moved[:, None] - deposits[None], axis=2)
        nearest = d.argmin(axis=1)
        paired = d[np.arange(len(recipe)), nearest] < 0.5 * scale * pitch
        if paired.sum() < MIN_PAIRS:
            break
        refit, _ = cv2.estimateAffinePartial2D(
            recipe[paired].astype(np.float32), deposits[nearest[paired]].astype(np.float32), method=cv2.LMEDS,
        )
        if refit is None:
            break
        converged = np.allclose(refit, m, atol=1e-3)
        m = refit.astype(np.float64)
        if converged:
            break
    return m


def register(blobs: list[dict], profile: Profile) -> tuple[Profile, Registration]:
    n = len(profile.points)
    if n < 2 or len(blobs) < MIN_PAIRS:
        return profile, Registration(applied=False, positions=n)

    recipe = np.array([[p.cx, p.cy] for p in profile.points], dtype=np.float64)
    radii = np.array([p.r for p in profile.points], dtype=np.float64)
    every_blob = np.array([[b["cx"], b["cy"]] for b in blobs], dtype=np.float64)
    areas = np.array([b["area"] for b in blobs], dtype=np.float64)
    is_deposit = areas > SPECK_FRACTION * np.median(areas)
    deposits = every_blob[is_deposit]

    framed_matched = _reached(recipe, radii, every_blob)
    as_framed = Registration(
        applied=False, positions_matched=framed_matched, positions_matched_as_framed=framed_matched, positions=n,
    )
    recipe_pitch = _pitch(recipe)
    if len(deposits) < MIN_PAIRS or recipe_pitch <= 0:
        return profile, as_framed
    pitch_scale = _pitch(deposits) / recipe_pitch
    framed_like_recipe = (
        framed_matched >= max(MIN_PAIRS, math.ceil(FRAMED_SHARE * n)) and abs(pitch_scale - 1) <= SCALE_TOLERANCE
    )
    if framed_like_recipe:
        return profile, as_framed

    nominal_area = float(np.median(math.pi * radii**2))
    size_scale = math.sqrt(float(np.median(areas[is_deposit])) / nominal_area) if nominal_area else pitch_scale
    scales = sorted({round(base * nudge, 4) for base in (pitch_scale, size_scale) for nudge in SCALE_NUDGES})

    m = _best_hypothesis(recipe, radii, deposits, scales)
    if m is None:
        return profile, as_framed
    m = _refine(m, recipe, deposits, recipe_pitch)
    scale = math.hypot(m[0, 0], m[1, 0])

    moved = _apply(m, recipe)
    matched = _reached(moved, radii * scale, every_blob)
    gain_needed = max(2, math.ceil(GAIN_SHARE * n))
    if matched - framed_matched < gain_needed or matched < max(MIN_PAIRS, math.ceil(ACCEPT_SHARE * n)):
        return profile, as_framed

    points = [
        ProfilePoint(index=p.index, cx=float(q[0]), cy=float(q[1]), r=p.r * scale)
        for p, q in zip(profile.points, moved, strict=True)
    ]
    return replace(profile, points=points), Registration(
        applied=True, scale=scale, rotation_deg=math.degrees(math.atan2(m[1, 0], m[0, 0])),
        shift_px=(float(m[0, 2]), float(m[1, 2])), positions_matched=matched,
        positions_matched_as_framed=framed_matched, positions=n,
    )
