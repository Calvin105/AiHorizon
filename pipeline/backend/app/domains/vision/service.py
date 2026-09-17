"""Step 3: analyse symptoms. Orchestrates detect() -> quality gate ->
signal derivation -> magnitude bucketing into the one result the rest of
the pipeline reads (stored on Case.vision_result, folded into
Case.fingerprint.signals)."""

from dataclasses import dataclass

from detect import detect

from app.domains.vision.magnitude import bucket_magnitude
from app.domains.vision.quality import quality_gate
from app.domains.vision.signals import derive_signals

CHANCE_P_THRESHOLD = 0.05


@dataclass
class VisionResult:
    quality_ok: bool
    quality_reason: str | None
    cv_output: dict
    signals: dict[str, float | int]
    magnitude: str
    small_then_big_above_chance: bool
    """The step-8 option-8 signature ('a small dot, then an oversized one')
    fires only above chance — DESIGN.md's fix for the 1-of-4-at-p=0.62
    false-positive. Only vision/detect/ can set this; the picker never
    offers it (DESIGN.md W3)."""


def run_vision(raw_image: bytes, profile_data: dict | None, spec_limit: str | None) -> VisionResult:
    cv_output = detect(raw_image, profile_data)
    ok, reason = quality_gate(cv_output)

    if not ok:
        return VisionResult(
            quality_ok=False, quality_reason=reason, cv_output=cv_output,
            signals={}, magnitude="unknown", small_then_big_above_chance=False,
        )

    signals = derive_signals(cv_output)
    magnitude = bucket_magnitude(signals.get("size_cv"), spec_limit)  # type: ignore[arg-type]

    chance_p = signals.get("small_then_big_chance_p")
    above_chance = (
        signals.get("small_then_big_count", 0) > 0
        and chance_p is not None
        and chance_p < CHANCE_P_THRESHOLD
    )

    return VisionResult(
        quality_ok=True, quality_reason=None, cv_output=cv_output,
        signals=signals, magnitude=magnitude, small_then_big_above_chance=bool(above_chance),
    )
