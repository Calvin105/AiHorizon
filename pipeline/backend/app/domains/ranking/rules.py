"""Step 5 pass 1's rule set: one CauseRule list per golden/causes.json
entry. DESIGN.md W2's fix over the old pack is applied throughout: signal
rules scale continuously by distance from a chance/nominal baseline
instead of firing at full weight the instant a fixed threshold is
crossed, so 0.16 and 0.49 on size_cv no longer score the same.

Grounded in the same manual sections golden/causes.json cites — the
`source` on each rule is what causes/compare.py shows as the citation for
step 4, and what a human can argue with, per DESIGN.md's design goal.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

Fingerprint = dict  # {"axes": {...}, "signals": {...}} — see cases/schema.py


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def ramp(value: float, baseline: float, spread: float, cap: float = 1.5) -> float:
    """0 at/below baseline, ramping linearly to `cap` as value moves one
    `spread` past it. This is the "how far past chance/nominal" scaling
    DESIGN.md W2 asks for, in place of a binary threshold."""
    if spread <= 0:
        return 0.0
    return clamp((value - baseline) / spread, 0.0, cap)


@dataclass(frozen=True)
class Weighed:
    """A rule's test, plus the weight it was given from the manual. Signal
    rules scale that weight by how far the reading is past normal, so for
    them it is the weight at strength 1. This is the number an engineer can
    change on the rules page (ranking/weights.py)."""

    weight: float
    test: Callable[[Fingerprint], float | None]  # logit contribution, or None if it doesn't fire

    def __call__(self, fp: Fingerprint) -> float | None:
        return self.test(fp)


@dataclass(frozen=True)
class CauseRule:
    label: str
    detail: str
    source: str
    evaluate: Weighed
    kind: Literal["signal", "answer"] = "answer"


def _signal(fp: Fingerprint, key: str) -> float | None:
    value = fp.get("signals", {}).get(key)
    return value if isinstance(value, int | float) else None


def _axis(fp: Fingerprint, axis: str) -> str | list[str] | None:
    return fp.get("axes", {}).get(axis)


def _has(fp: Fingerprint, axis: str, value: str) -> bool:
    got = _axis(fp, axis)
    if isinstance(got, list):
        return value in got
    return got == value


def _followup_is(fp: Fingerprint, question_id: str, value: str) -> bool:
    """An adaptive follow-up's answer (intake/followups.py). Kept out of
    `axes` so it ranks but never enters case matching."""
    return (fp.get("followups") or {}).get(question_id) == value


# ---- reusable signal rules -------------------------------------------------

def _size_cv_instability(weight: float) -> Weighed:
    def rule(fp: Fingerprint) -> float | None:
        cv = _signal(fp, "size_cv")
        if cv is None:
            return None
        strength = ramp(cv, baseline=0.15, spread=0.20)
        return weight * strength if strength > 0 else None
    return Weighed(weight, rule)


def _carryover_pattern(weight: float) -> Weighed:
    def rule(fp: Fingerprint) -> float | None:
        count = _signal(fp, "small_then_big_count")
        p = _signal(fp, "small_then_big_chance_p")
        if not count or p is None or p >= 0.05:
            return None
        # Further below the 0.05 chance line = stronger evidence, capped.
        strength = clamp(1.0 + (0.05 - p) / 0.05, 1.0, 2.0)
        return weight * strength
    return Weighed(weight, rule)


def _irregular_deposits(weight: float) -> Weighed:
    """Counts distorted deposits rather than averaging circularity over the
    array — the mean hides a few bad dots among many good ones (see
    vision/signals.py). Same ramp as missing deposits: one is weak
    evidence, three is full weight."""
    def rule(fp: Fingerprint) -> float | None:
        count = _signal(fp, "irregular_count")
        if not count:
            return None
        strength = ramp(float(count), baseline=0.0, spread=3.0)
        return weight * strength if strength > 0 else None
    return Weighed(weight, rule)


def _missing_without_carryover(weight: float) -> Weighed:
    def rule(fp: Fingerprint) -> float | None:
        missing = _signal(fp, "missing_count")
        p = _signal(fp, "small_then_big_chance_p")
        if not missing or (p is not None and p < 0.05):
            return None  # the carryover rule already explains this pattern better
        strength = ramp(float(missing), baseline=0.0, spread=3.0)
        return weight * strength if strength > 0 else None
    return Weighed(weight, rule)


def _answer(weight: float) -> Weighed:
    def rule(_fp: Fingerprint) -> float | None:
        return weight
    return Weighed(weight, rule)


# ---- cause definitions ------------------------------------------------------
# Each tuple: (rule, only fires when predicate(fp) is true)

def _r(label: str, detail: str, source: str, evaluate: Weighed, kind: Literal["signal", "answer"] = "answer") -> CauseRule:
    return CauseRule(label=label, detail=detail, source=source, evaluate=evaluate, kind=kind)


def _gated(predicate, make_rule: Weighed) -> Weighed:
    """Wrap an answer-triggered rule so it only evaluates when predicate(fp)."""
    def evaluate(fp: Fingerprint) -> float | None:
        return make_rule(fp) if predicate(fp) else None
    return Weighed(make_rule.weight, evaluate)


CAUSE_RULES: dict[str, list[CauseRule]] = {
    "volume_too_small_carryover": [
        _r(
            "Small dot then oversized dot, above chance",
            "The next deposition point measured oversized after a small/missing one — matc82's carryover signature, and above the chance baseline for this dispense order.",
            "matc82 sec 3.5 p.18-19",
            _carryover_pattern(2.2), kind="signal",
        ),
        # matc82 sec 3.5's own remedy is more volume — "increase the dispense
        # time" — so that is what counts as evidence here. This used to be
        # "purging helps", which the section never says.
        _r(
            "Response: turning pressure or time up helps",
            "matc82's fix for big dot / small dot is a larger dispensed volume: increase the dispense time.",
            "matc82 sec 3.5 p.19",
            _gated(lambda fp: _has(fp, "response", "raise_pressure_or_time"), _answer(1.0)),
        ),
    ],
    "pressure_time_instability": [
        _r(
            "Size varies shot to shot, no clear pattern",
            "Shot-to-shot volume variability is the signature of an unstable pressure-time system.",
            "matc82 sec 2.1 p.6",
            _size_cv_instability(1.4), kind="signal",
        ),
        _r(
            "Footprint follows the machine or head",
            "Points at the dispense unit itself rather than material or tooling.",
            "matc82 sec 2.1 p.6",
            _gated(lambda fp: _has(fp, "footprint", "machine"), _answer(1.0)),
        ),
        _r(
            "Plant air supply changed or unreliable",
            "Pressure-time systems draw directly on plant air; a change there changes every shot.",
            "matc82 sec 2.1 p.6",
            _gated(lambda fp: _has(fp, "inputs", "air_supply_changed"), _answer(1.3)),
        ),
        _r(
            "Response: raising pressure/time helps",
            "Compensating with more pressure or time is consistent with an underlying instability.",
            "brief p.3",
            _gated(lambda fp: _has(fp, "response", "raise_pressure_or_time"), _answer(0.5)),
        ),
    ],
    "air_in_fluid_path": [
        _r(
            "Occasional, comes and goes",
            "The brief links air entrapment to volume that changes occasionally, not continuously.",
            "brief p.3",
            _gated(lambda fp: _has(fp, "trajectory", "random"), _answer(1.0)),
        ),
        _r(
            "Only on the first shots after a pause",
            "Air pockets settle during a pause and clear a few shots in — a distinctive time signature.",
            "brief p.3",
            _gated(lambda fp: _has(fp, "trajectory", "after_pause"), _answer(1.3)),
        ),
        _r(
            "Response: purging or a new syringe helps",
            "Purging expels trapped air; a fresh syringe removes it entirely.",
            "brief p.4",
            _gated(
                lambda fp: _has(fp, "response", "purge_or_prime") or _has(fp, "response", "new_syringe"),
                _answer(1.1),
            ),
        ),
        _r(
            "Syringe nearly empty",
            "Air is most likely to enter the fluid path as a syringe runs low.",
            "brief p.3",
            _gated(lambda fp: _has(fp, "inputs", "syringe_nearly_empty"), _answer(0.8)),
        ),
    ],
    "material_rheology_change": [
        _r(
            "Gradual, worse over hours or days",
            "Curing, settling, or ambient drift changes viscosity gradually rather than in a step.",
            "matc82 sec 2.5 p.8",
            _gated(lambda fp: _has(fp, "trajectory", "gradual"), _answer(1.1)),
        ),
        _r(
            "Near or past out-time",
            "A material's rheology alters over time as it cures, changing flow rate and so the dispensed "
            "volume — the longer it has been out, the further it has moved.",
            "matc82 sec 2.5 p.8",
            _gated(lambda fp: _has(fp, "inputs", "near_out_time"), _answer(1.4)),
        ),
        _r(
            "Room temperature changed",
            "Ambient temperature changes the material's rheology in the cartridge, and so the dispensed "
            "volume. (matc82 adds that humidity has little effect on sealed cartridges.)",
            "matc82 sec 2.9.1 p.13",
            _gated(lambda fp: _has(fp, "inputs", "ambient_changed"), _answer(1.0)),
        ),
        _r(
            "Footprint follows the material or lot",
            "Points at the fluid itself rather than the machine or tooling.",
            "brief p.3",
            _gated(lambda fp: _has(fp, "footprint", "material"), _answer(0.9)),
        ),
        _r(
            "Response: warming up helps",
            "Warm-up recovering the process is consistent with a viscosity effect — matc82's answer to "
            "ambient drift is a heated nozzle holding the material at a constant temperature.",
            "matc82 sec 2.9.1 p.13",
            _gated(lambda fp: _has(fp, "response", "let_it_warm_up"), _answer(1.0)),
        ),
    ],
    "nozzle_blockage": [
        _r(
            "Irregular deposit shapes (circularity below 0.80)",
            "A partially blocked needle distorts the flow, and so the deposit's silhouette.",
            "matc82 sec 3.1 p.15-16",
            _irregular_deposits(1.2), kind="signal",
        ),
        _r(
            "Missing deposits without the carryover pattern",
            "Deposits are dropped outright, but not in the small-then-big pattern that points to carryover instead.",
            "matc82 sec 3.1 p.15-16",
            _missing_without_carryover(1.0), kind="signal",
        ),
        _r(
            "Footprint follows the nozzle, needle, or valve",
            "Points directly at the tooling most likely to carry a partial blockage.",
            "matc82 sec 3.1 p.15-16",
            _gated(lambda fp: _has(fp, "footprint", "tooling"), _answer(1.3)),
        ),
        _r(
            "Response: wiping or changing the needle helps",
            "Clearing or replacing the needle is the direct remedy for a blockage.",
            "matc82 sec 3.1 p.15-16",
            _gated(lambda fp: _has(fp, "response", "wipe_or_change_needle"), _answer(1.4)),
        ),
    ],
    "dispense_height_or_board_bending": [
        _r(
            "Shape changes across the board",
            "matc82 describes squat deposits where the needle sits low and tall ones where it sits high — a position-dependent shape effect.",
            "matc82 sec 2.8 p.12",
            _gated(lambda fp: _has(fp, "signature", "shape_changes_across_board"), _answer(1.8)),
        ),
        _r(
            "It has always been like this",
            "A process that was never capable routes to recipe/geometry, not to wear or contamination.",
            "matc82 sec 2.7 p.11",
            _gated(lambda fp: _has(fp, "trajectory", "always_been_like_this"), _answer(1.2)),
        ),
        _r(
            "Footprint follows the product or program",
            "Points at the recipe/geometry rather than a component that can wear or clog.",
            "matc82 sec 2.7 p.11",
            _gated(lambda fp: _has(fp, "footprint", "recipe"), _answer(1.0)),
        ),
    ],
    "equipment_condition": [
        _r(
            "Gradual, worse over hours or days",
            "General wear degrades performance gradually rather than in a step.",
            "matc82 sec 2.10 p.13",
            _gated(lambda fp: _has(fp, "trajectory", "gradual"), _answer(0.6)),
        ),
        _r(
            "Footprint follows the machine or head",
            "Points at the equipment itself.",
            "brief p.4",
            _gated(lambda fp: _has(fp, "footprint", "machine"), _answer(0.7)),
        ),
        _r(
            "Response: restarting or re-homing helps",
            "Recovering after a restart/re-home points at equipment state rather than material or recipe.",
            "matc82 sec 2.10 p.13",
            _gated(lambda fp: _has(fp, "response", "restart_or_rehome"), _answer(1.2)),
        ),
    ],
}

# ---- adaptive follow-ups (intake/followups.py) --------------------------------
# Asked only when their answers can move the ranking; each answer is evidence
# with its own source, exactly like a spine answer.

def _fu(question_id: str, value: str, weight: float) -> Weighed:
    return _gated(lambda fp: _followup_is(fp, question_id, value), _answer(weight))


CAUSE_RULES["volume_too_small_carryover"] += [
    _r("Next dot after a small one is oversized",
       "Seen by eye: a very small or missing dot followed by an oversized one — the hallmark matc82 describes.",
       "matc82 sec 3.5 p.18-19", _fu("next_dot", "oversized", 1.6)),
    _r("Next dot after a small one is normal",
       "The dot after a small one comes out normal size — not the big dot / small dot pattern.",
       "matc82 sec 3.5 p.18-19", _fu("next_dot", "normal", -0.8)),
]
CAUSE_RULES["nozzle_blockage"] += [
    _r("Small or missing dot without the oversized follow-on",
       "Missed material that isn't caught by the next dot points to a restriction, not carryover.",
       "matc82 sec 3.1 p.15-16", _fu("next_dot", "normal", 0.4)),
]
CAUSE_RULES["dispense_height_or_board_bending"] += [
    _r("Worse in one area of the board",
       "A board bent by its clamps changes the practical dispense height, and so the deposit shape, across its area.",
       "matc82 sec 2.8 p.11-12", _fu("location", "one_area", 1.2)),
    _r("Started when the board, fixture or clamping changed",
       "Clamps out of line bend the board, and the bend can be much larger than the laminate's own warp.",
       "matc82 sec 2.8 p.11-12", _fu("recent_change", "fixture_changed", 1.1)),
    _r("Started when the needle changed",
       "The right dispense height is set from the needle's inner diameter, so a different needle needs it re-set.",
       "matc82 sec 2.7 p.11", _fu("recent_change", "needle_changed", 0.9)),
    _r("Started when the program was edited",
       "Dispense height, up height and dispense time are all programmed — a mistake there changes every deposit.",
       "matc82 sec 2.11 p.14", _fu("recent_change", "program_changed", 0.6)),
]
CAUSE_RULES["material_rheology_change"] += [
    _r("Started with a new lot or syringe",
       "A new lot or syringe is a change of material — the brief's \"the material viscosity may have changed\".",
       "brief p.3", _fu("recent_change", "new_material", 0.9)),
    _r("Every position affected alike",
       "A change in the material's flow rate shifts every deposit the same way, wherever it lands.",
       "matc82 sec 2.5 p.8", _fu("location", "everywhere_same", 0.4)),
]
CAUSE_RULES["air_in_fluid_path"] += [
    _r("Started with a new syringe or lot",
       "A freshly loaded syringe is where trapped air gets in.",
       "brief p.3", _fu("recent_change", "new_material", 0.5)),
    _r("Random spots, different each board",
       "The brief ties air to volume that changes occasionally rather than continuously.",
       "brief p.3", _fu("location", "random_spots", 0.5)),
]
CAUSE_RULES["pressure_time_instability"] += [
    _r("Pressure gauge wanders during a run",
       "In a pressure-time system the dispensed volume follows the pressure, so a wandering supply moves every shot.",
       "matc82 sec 2.1 p.6", _fu("pressure_gauge", "wanders", 1.3)),
    _r("Pressure gauge steady",
       "A steady supply argues against shot-to-shot pressure variation.",
       "matc82 sec 2.1 p.6", _fu("pressure_gauge", "steady", -0.6)),
    _r("Random spots, different each board",
       "Pressure-time systems are the less repeatable kind — scatter with no position pattern fits.",
       "matc82 sec 2.1 p.6", _fu("location", "random_spots", 0.3)),
]
CAUSE_RULES["equipment_condition"] += [
    _r("Started after the machine was serviced",
       "Something changed in the dispensing system itself — the brief's cue that it needs inspecting.",
       "brief p.4", _fu("recent_change", "machine_serviced", 1.0)),
]

# "It has always been like this" argues against wear/contamination causes —
# DESIGN.md is explicit that this is a different case class. Modeled as
# negative-weight rules on the causes it argues against, so the evidence is
# visible in step 4's comparison rather than a silent exclusion.
CAUSE_RULES["nozzle_blockage"].append(
    _r(
        "Always been like this (argues against wear/contamination)",
        "A process that was never capable is a setup/geometry issue, not a developing blockage.",
        "matc82 sec 2.7 p.11",
        _gated(lambda fp: _has(fp, "trajectory", "always_been_like_this"), _answer(-0.8)),
    )
)
CAUSE_RULES["equipment_condition"].append(
    _r(
        "Always been like this (argues against wear/contamination)",
        "A process that was never capable is a setup/geometry issue, not equipment that has degraded.",
        "matc82 sec 2.7 p.11",
        _gated(lambda fp: _has(fp, "trajectory", "always_been_like_this"), _answer(-0.8)),
    )
)
