"""Who writes which half of the fingerprint.

The interview owns `axes` and `axis_notes`. The photo owns `signals`, plus
the one axis value only a measurement can set: the image-only
`small_then_big` signature. Each writer replaces its own half and leaves
the other alone.

Both helpers return a new dict on purpose. SQLAlchemy's plain JSON column
only notices the assignment of a *different* object, so editing the stored
dict in place and assigning it back is silently never saved — which is how
every photo retaken after a refused one used to lose its measurements.
"""

from app.domains.intake.spec import IMAGE_ONLY_SIGNATURE_VALUE


def _picked_signature(axes: dict) -> list[str]:
    return [v for v in (axes.get("signature") or []) if v != IMAGE_ONLY_SIGNATURE_VALUE]


def with_measurement(fingerprint: dict | None, signals: dict, carryover_above_chance: bool) -> dict:
    """After a photo. Its signals replace the previous photo's wholesale —
    merging kept keys this photo didn't produce, such as an earlier image's
    carryover p-value, next to measurements they were never taken with."""
    previous = fingerprint or {}
    axes = dict(previous.get("axes") or {})
    signature = _picked_signature(axes)
    if carryover_above_chance:
        signature.append(IMAGE_ONLY_SIGNATURE_VALUE)
    axes["signature"] = signature
    return {**previous, "axes": axes, "signals": dict(signals)}


def with_answers(fingerprint: dict | None, incoming: dict) -> dict:
    """After an interview save. The client's axes and notes; the measured
    half exactly as the last photo left it, whatever the client sent."""
    previous = fingerprint or {}
    axes = dict(incoming.get("axes") or {})
    signature = _picked_signature(axes)
    if IMAGE_ONLY_SIGNATURE_VALUE in ((previous.get("axes") or {}).get("signature") or []):
        signature.append(IMAGE_ONLY_SIGNATURE_VALUE)
    axes["signature"] = signature
    # A save that doesn't mention follow-ups leaves the ones on file alone.
    followups = incoming["followups"] if "followups" in incoming else (previous.get("followups") or {})
    return {
        **incoming, "axes": axes, "followups": dict(followups),
        "signals": dict(previous.get("signals") or {}),
    }
