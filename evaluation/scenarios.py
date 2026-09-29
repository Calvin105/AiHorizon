"""Scenario cards: for each cause, what the photo would look like and how
an operator on the line would plausibly answer the five questions.

Written from how each fault physically behaves (the sources cited on each
card), NOT from ranking/rules.py. That separation is the point: if these
cards were copied from the rule triggers, the diagnosis score would just
be the rules grading themselves. So each card deliberately includes
answers the rules do not reward — a starved-volume recipe really does
improve when the pressure is turned up, even though no rule says so — and
a miss on those is a finding about the rules, not noise.

Source of truth for every card: TEAM JUDGEMENT, informed by the cited
sections (DESIGN.md W1: team-judgement scenarios test consistency, not
correctness). Review these before quoting the numbers they produce.

Answer weights are relative plausibility within one axis. Option ids are
exactly the ones app/domains/intake/spec.py offers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.domains.intake.spec import DONT_KNOW_VALUE, QUESTIONS

Weighted = list[tuple[str, float]]


@dataclass(frozen=True)
class ImageRecipe:
    weight: float
    defects: list[str]
    params: dict[str, dict] = field(default_factory=dict)
    note: str = ""


@dataclass(frozen=True)
class Scenario:
    cause_id: str
    sources: str
    images: list[ImageRecipe]
    answers: dict[str, Weighted]


SCENARIOS: list[Scenario] = [
    Scenario(
        cause_id="volume_too_small_carryover",
        sources="matc82 sec 3.5 p.18-19 (Fig. 17), sec 2.6",
        images=[ImageRecipe(1.0, ["missing_carryover"], {"missing_carryover": {"miss_rate": 0.2}},
                            "starved dot, surplus lands on the next one")],
        answers={
            "signature": [("missing", 3), ("size_varies", 2), ("too_little", 1)],
            # Marginal volume is usually a recipe setting, so it has often
            # always been this way, or started with a program change.
            "trajectory": [("always_been_like_this", 2), ("sudden_step", 2), ("random", 1)],
            "footprint": [("recipe", 3), ("everywhere", 1), ("not_tested", 2)],
            "inputs": [("nothing_unusual", 3), ("new_lot_or_syringe", 1)],
            # More volume is the actual fix, so raising pressure/time helps.
            "response": [("raise_pressure_or_time", 3), ("purge_or_prime", 1), ("not_tried", 1)],
        },
    ),
    Scenario(
        cause_id="pressure_time_instability",
        sources="matc82 sec 2.1 p.6, sec 3.2 p.16; brief p.3",
        images=[ImageRecipe(1.0, ["inconsistent"], {"inconsistent": {"scale": (0.6, 1.45)}},
                            "shot-to-shot volume scatter, no order pattern")],
        answers={
            "signature": [("size_varies", 4), ("too_little", 1)],
            "trajectory": [("random", 3), ("near_syringe_end", 1), ("sudden_step", 1)],
            "footprint": [("machine", 3), ("everywhere", 1), ("not_tested", 2)],
            # Pressure-time volume also drifts with syringe fill level.
            "inputs": [("air_supply_changed", 2), ("nothing_unusual", 2), ("syringe_nearly_empty", 1)],
            "response": [("raise_pressure_or_time", 2), ("nothing_helps", 2), ("restart_or_rehome", 1)],
        },
    ),
    Scenario(
        cause_id="air_in_fluid_path",
        sources="brief p.3-4",
        images=[
            ImageRecipe(0.5, ["inconsistent"], {"inconsistent": {"scale": (0.7, 1.25)}},
                        "an air slug caught mid-array: mild scatter"),
            ImageRecipe(0.5, [], {}, "intermittent — this photo caught a good moment"),
        ],
        answers={
            "signature": [("size_varies", 3), ("missing", 1), ("too_little", 1)],
            "trajectory": [("random", 3), ("after_pause", 2), ("near_syringe_end", 1), ("sudden_step", 1)],
            "footprint": [("material", 2), ("not_tested", 2), ("everywhere", 1)],
            "inputs": [("new_lot_or_syringe", 2), ("syringe_nearly_empty", 2), ("nothing_unusual", 1)],
            "response": [("purge_or_prime", 3), ("new_syringe", 2)],
        },
    ),
    Scenario(
        cause_id="material_rheology_change",
        sources="matc82 sec 2.5 p.8, sec 2.9.1 p.13; brief p.3",
        # A viscosity change shifts every dot the same way. With nominal size
        # inferred from the median (README known limitation), a uniform
        # shift is invisible in one photo — so the image carries nothing.
        images=[ImageRecipe(1.0, [], {}, "uniform size shift: invisible without a recipe target")],
        answers={
            "signature": [("too_little", 2), ("too_much", 1), ("size_varies", 1)],
            "trajectory": [("gradual", 3), ("after_running_a_while", 1), ("sudden_step", 1)],
            "footprint": [("material", 3), ("everywhere", 1), ("not_tested", 1)],
            "inputs": [("near_out_time", 2), ("ambient_changed", 2), ("new_lot_or_syringe", 1)],
            "response": [("let_it_warm_up", 2), ("new_syringe", 2), ("raise_pressure_or_time", 1)],
        },
    ),
    Scenario(
        cause_id="nozzle_blockage",
        sources="matc82 sec 3.1 p.15-16; brief p.4",
        images=[
            ImageRecipe(0.5, ["abnormal_shape"], {"abnormal_shape": {"count": 3}},
                        "partial blockage distorts the flow"),
            ImageRecipe(0.5, ["ghost", "abnormal_shape"], {"ghost": {"count": 2}, "abnormal_shape": {"count": 2}},
                        "some shots barely come out"),
        ],
        answers={
            "signature": [("wrong_shape", 2), ("too_little", 2), ("missing", 2)],
            # Material curing in the tip during idle time blocks it.
            "trajectory": [("sudden_step", 2), ("gradual", 2), ("after_pause", 1)],
            "footprint": [("tooling", 4), ("not_tested", 2)],
            "inputs": [("nothing_unusual", 3), ("near_out_time", 1)],
            "response": [("wipe_or_change_needle", 4), ("purge_or_prime", 2)],
        },
    ),
    Scenario(
        cause_id="dispense_height_or_board_bending",
        sources="matc82 sec 2.7 p.11, sec 2.8 p.12 (Figs. 9-10)",
        # The generator has no position-dependent shape operator, so the
        # closest it can draw is a few flooded, squat deposits.
        images=[
            ImageRecipe(0.5, ["overrun"], {"overrun": {"count": 3}}, "needle low: squat, flooded deposits"),
            ImageRecipe(0.5, [], {}, "height fault the photo does not show"),
        ],
        answers={
            "signature": [("shape_changes_across_board", 2), ("spread_or_smeared", 2), ("too_much", 1),
                          ("wrong_shape", 1)],
            "trajectory": [("always_been_like_this", 2), ("sudden_step", 2)],
            "footprint": [("recipe", 2), ("machine", 1), ("not_tested", 1)],
            "inputs": [("nothing_unusual", 4)],
            "response": [("nothing_helps", 2), ("restart_or_rehome", 1), ("not_tried", 2)],
        },
    ),
    Scenario(
        cause_id="equipment_condition",
        sources="matc82 sec 2.10 p.13; brief p.4",
        images=[
            ImageRecipe(0.5, ["inconsistent"], {"inconsistent": {"scale": (0.75, 1.25)}}, "worn valve: mild scatter"),
            ImageRecipe(0.5, [], {}, "wear the photo does not show yet"),
        ],
        answers={
            "signature": [("size_varies", 2), ("too_little", 1), ("wrong_shape", 1)],
            "trajectory": [("gradual", 3), ("after_running_a_while", 2), ("random", 1)],
            "footprint": [("machine", 3), ("not_tested", 2)],
            "inputs": [("nothing_unusual", 4)],
            "response": [("restart_or_rehome", 2), ("nothing_helps", 2), ("not_tried", 1)],
        },
    ),
]

PATTERNS = ["area", "grid_landmark", "perimeter", "pattern"]
"""line_trace is left out of diagnosis: 6 dots in a single row is too few
for a size-spread signal, and the README already lists it as a known miss."""

_ALL_OPTIONS = {q.axis: [o.value for o in q.options] for q in QUESTIONS}
_MULTI = {q.axis for q in QUESTIONS if q.kind == "multi"}
_EXCLUSIVE = {"nothing_unusual", DONT_KNOW_VALUE}


def _draw(rng: np.random.Generator, weighted: Weighted) -> str:
    values, weights = zip(*weighted, strict=True)
    p = np.array(weights, dtype=float)
    return str(rng.choice(values, p=p / p.sum()))


def pick_image(rng: np.random.Generator, scenario: Scenario) -> ImageRecipe:
    weights = np.array([r.weight for r in scenario.images], dtype=float)
    return scenario.images[int(rng.choice(len(scenario.images), p=weights / weights.sum()))]


def simulate_answers(rng: np.random.Generator, scenario: Scenario, reliability: float) -> dict:
    """One operator's interview. With probability `reliability` an axis is
    answered from the card; otherwise the operator picks any option at
    random, "Don't know" included — misremembering, guessing, or answering
    a different question than the one asked."""
    axes: dict[str, str | list[str]] = {}
    for axis, options in _ALL_OPTIONS.items():
        if rng.random() < reliability:
            value = _draw(rng, scenario.answers[axis])
            if axis in _MULTI and value not in _EXCLUSIVE and rng.random() < 0.3:
                # Sometimes a second condition genuinely co-occurs.
                extra = _draw(rng, scenario.answers[axis])
                values = [value] if extra in _EXCLUSIVE or extra == value else [value, extra]
            else:
                values = [value]
        else:
            values = [str(rng.choice([*options, DONT_KNOW_VALUE]))]
        axes[axis] = values if axis in _MULTI else values[0]
    return axes
