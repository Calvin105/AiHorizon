"""Step 7's re-measure: is the photo after the fix in spec on everything a
photo can measure, and what happened to the signal that was out before?

"Back in spec" used to mean size_cv alone. A board with a deposit still
missing measures a perfectly tight size spread — the missing dot has no
area to vary — so it passed. In spec now means what evaluation/ already
calls a good photo: spread inside the limit, nothing missing, no irregular
deposits, and no carryover pattern above chance.
"""

CHANCE_P = 0.05

#: The measured signal each cause is decided by, most telling first. The
#: first of these that was out of spec before the fix is the one the
#: verification headline reports as "the deciding signal".
DECIDING_SIGNALS: dict[str, tuple[str, ...]] = {
    "volume_too_small_carryover": ("small_then_big_chance_p", "missing_count", "size_cv"),
    "pressure_time_instability": ("size_cv",),
    "air_in_fluid_path": ("size_cv", "missing_count"),
    "material_rheology_change": ("size_cv",),
    "nozzle_blockage": ("missing_count", "irregular_count", "size_cv"),
    "dispense_height_or_board_bending": ("size_cv", "irregular_count"),
    "equipment_condition": ("size_cv", "missing_count"),
}

CHECKED_SIGNALS = ("size_cv", "missing_count", "irregular_count", "small_then_big_chance_p")


def _within(signal: str, value: float | None, limit: float) -> bool:
    if signal == "size_cv":
        return value is not None and value <= limit
    if signal == "small_then_big_chance_p":
        return value is None or value >= CHANCE_P  # no small dots at all is no pattern
    return not value  # counts: zero, or never measured as non-zero


def _limit_text(signal: str, limit: float) -> str:
    if signal == "size_cv":
        return f"≤ {limit:g}"
    if signal == "small_then_big_chance_p":
        return f"no pattern (p ≥ {CHANCE_P:g})"
    return "0"


def build_verification(
    before: dict, after: dict | None, limit: float, cause_id: str | None,
    *, deposits_measured: int | None, shots_reported: int | None,
) -> dict:
    """`before` is the case's fingerprint signals from the photo taken before
    the fix; `after` the fresh photo's, or None when its quality gate failed."""
    checks = []
    for signal in CHECKED_SIGNALS:
        b = before.get(signal)
        a = after.get(signal) if after else None
        checks.append({
            "signal": signal, "before": b, "after": a, "limit": _limit_text(signal, limit),
            "was_out": bool(before) and not _within(signal, b, limit),
            "ok": after is not None and _within(signal, a, limit),
        })

    was_out = {c["signal"] for c in checks if c["was_out"]}
    preference = DECIDING_SIGNALS.get(cause_id or "", ()) + CHECKED_SIGNALS
    deciding = next((s for s in preference if s in was_out), "size_cv")

    return {
        "signal": deciding,
        "before": before.get(deciding),
        "after": after.get(deciding) if after else None,
        "in_spec": after is not None and all(c["ok"] for c in checks),
        "checks": checks,
        "size_cv_limit": limit,
        "deposits_measured": deposits_measured,
        # The photo shows one moment; whether the fix held over a run of shots
        # is the operator's report, and is labelled as theirs.
        "shots_measured": shots_reported,
        "shots_source": "operator",
        "recurred_after_days": None,
    }
