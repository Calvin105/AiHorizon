"""Per-dot symptom classification: turns an aligned measurement into the
same kind of tag a process engineer would write on an inspection sheet.

Important scope note: this predicts *symptoms* the geometry actually shows
(missing, oversized, undersized, irregular, misaligned, extra,
possibly_fused) -- not the full defect taxonomy in docs/personal/img_type.txt
directly. Several causes share a symptom by design: overrun and
double_dispense both read as "oversized"; bridging and dragged both read as
"possibly_fused". Telling those apart needs shape descriptors (concavity,
elongation direction, lattice-span counting) this module doesn't compute
yet. Air bubble, satellite, contamination speck, and ghost are not
classified at all here for the same reason test_metrology.py documents them
as gaps: they're texture- or noise-floor-level, and this module only sees
silhouette geometry. Run evaluate.py to see the current generator-tag ->
symptom correspondence measured against the actual generated dataset,
rather than trusting this comment.
"""

from __future__ import annotations

import math

from .align import Match

CIRCULARITY_IRREGULAR = 0.80
UNDERSIZED_LIMIT = 0.70
OVERSIZED_LIMIT = 1.40
MISALIGN_FACTOR = 0.6  # deviation beyond this * nominal radius is flagged misaligned
#: How far a deposit's area can sit from nominal and still be the right
#: size. The same 15% as the demo profiles' size-spread spec (size_cv < 0.15).
SIZE_TOLERANCE = 0.15


def classify_point(match: Match) -> dict:
    p = match.point
    nominal_area = math.pi * p.r**2

    if match.blob is None:
        tags = ["possibly_fused"] if match.fused_with is not None else ["missing"]
        return {
            "index": p.index, "cx": round(p.cx, 2), "cy": round(p.cy, 2),
            "tags": tags, "fused_with": match.fused_with,
        }

    b = match.blob
    tags: list[str] = []
    ratio = b["area"] / nominal_area if nominal_area else 1.0
    if ratio > OVERSIZED_LIMIT:
        tags.append("oversized")
    elif ratio < UNDERSIZED_LIMIT:
        tags.append("undersized")
    if b["circularity"] < CIRCULARITY_IRREGULAR:
        tags.append("irregular")
    if match.deviation > max(p.r * MISALIGN_FACTOR, 3.0):
        tags.append("misaligned")

    return {
        "index": p.index, "cx": round(b["cx"], 2), "cy": round(b["cy"], 2), "tags": tags,
        "area_ratio": round(ratio, 3), "circularity": round(b["circularity"], 3),
        "deviation_px": round(match.deviation, 2),
    }


def classify_extra(blob: dict) -> dict:
    """A blob with no matching profile position at all -- stray material."""
    return {"cx": round(blob["cx"], 2), "cy": round(blob["cy"], 2), "tags": ["extra"], "area": round(blob["area"], 1)}


def classify_array(dots: list[dict]) -> None:
    """Inconsistent volume is a property of the *array*, not any one dot,
    so classify_point, which judges one dot at a time, can never catch it.
    This pass runs after, over every matched dot in one image.

    Rule: if the same image already has at least one dot flagged oversized
    AND at least one flagged undersized, that's the actual fingerprint of
    scatter -- every other size-affecting defect here only ever pushes area
    in one direction (overrun, carryover, double-dispense all inflate;
    none shrink), so seeing both directions at once isn't explainable by
    any single-cause defect. A plain coefficient-of-variation over the
    whole array was tried first and rejected: one unrelated oversized
    outlier (e.g. a single overrun dot) could inflate it enough to
    wrongly re-flag every genuinely clean dot in that image, which is
    exactly the false-positive problem the 2026-09-14 fixes just removed.

    Inside a scattered batch, a dot is marked inconsistent only if its own
    size is off nominal, beyond SIZE_TOLERANCE. A dot whose size happens to
    land on nominal is the right size, even in a scattered batch. This pass
    used to mark every unflagged dot, because the synthetic ground truth
    stamps the tag on every dot it rescaled, so a dot at 1.01x nominal was
    drawn as a defect. The array-level verdict doesn't rest on these tags:
    ranking reads size_cv, which is computed from every dot's area.
    Mutates `dots` in place.
    """
    has_oversized = any("oversized" in d["tags"] for d in dots)
    has_undersized = any("undersized" in d["tags"] for d in dots)
    if not (has_oversized and has_undersized):
        return
    for d in dots:
        if "area_ratio" in d and not d["tags"] and abs(d["area_ratio"] - 1) > SIZE_TOLERANCE:
            d["tags"].append("inconsistent")
