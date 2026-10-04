"""What symptom(s) each generator-assigned defect tag is expected to produce.

This codifies the correspondence evaluate.py's baseline run actually found
(see docs/vision_detection_log.md) rather than a theoretical ideal, so
"correct" means "matches known current behaviour," not "matches a target we
haven't built yet." Shared by evaluate.py (for the aggregate report) and
visualize.py (for per-dot right/wrong coloring), so both use one definition.

Classes not listed here (air_bubble, satellite, contamination_speck) are
known-undetectable by this silhouette-only pipeline -- see
vision/detect/classify.py's docstring -- and are treated as "not yet
judged" rather than right or wrong.
"""

from __future__ import annotations

from .classify import SIZE_TOLERANCE

EXPECTED_SYMPTOMS: dict[str, set[str]] = {
    "missing": {"missing", "possibly_fused"},
    "carryover_big": {"oversized"},
    "overrun": {"oversized", "irregular"},
    "abnormal_shape": {"irregular"},
    "misaligned": {"misaligned", "missing"},  # see known issue: severe drift reads as missing
    "double_dispense": {"oversized", "irregular"},
    "line_end_defect": {"oversized", "irregular"},
    "line_start_defect": {"missing", "possibly_fused"},
    "ghost": {"missing", "possibly_fused"},
    "inconsistent": {"oversized", "undersized", "inconsistent"},
    "smearing": {"oversized", "irregular", "misaligned"},
    "stringing": {"irregular", "oversized", "misaligned"},
    # Fusing two positions is inherently ambiguous about which position
    # "owns" the problem -- see known issue: neighbour drag-down. Any
    # non-empty prediction on either position is treated as plausible.
    "bridging": {"missing", "possibly_fused", "oversized", "irregular", "misaligned"},
    "dragged": {"missing", "possibly_fused", "oversized", "irregular", "misaligned"},
}

# Tags this pipeline is known not to be able to detect yet -- not scored.
NOT_YET_JUDGED = {"air_bubble", "satellite", "contamination_speck"}


def effective_gt_tags(gt_dot: dict, nominal_r: float | None) -> list[str]:
    """The generator stamps "inconsistent" on every dot it rescaled,
    including the ones whose random scale landed on nominal. Those dots are
    the right size, so they're scored as good: the detector is right not to
    flag them. Measured from the radius the generator actually drew."""
    tags = list(gt_dot.get("tags", []))
    r = gt_dot.get("r")
    if "inconsistent" not in tags or not r or not nominal_r:
        return tags
    if abs((r / nominal_r) ** 2 - 1) <= SIZE_TOLERANCE:
        return [t for t in tags if t != "inconsistent"]
    return tags


def is_plausible(gt_tags: list[str], predicted_tags: list[str]) -> bool | None:
    """True/False if this ground-truth tag set can be judged; None if it's a
    known not-yet-detectable class and shouldn't be scored either way."""
    tags = gt_tags or ["good"]
    if all(t in NOT_YET_JUDGED for t in tags):
        return None
    if tags == ["good"]:
        return not predicted_tags
    expected: set[str] = set()
    for t in tags:
        expected |= EXPECTED_SYMPTOMS.get(t, set())
    if not expected:
        return None  # no expectation registered for this tag -- don't judge
    return any(p in expected for p in predicted_tags)
