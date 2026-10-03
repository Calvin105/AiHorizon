"""The rule table on the home page: every answer and measurement the rule
engine knows, against every cause it moves, with the weight and the page.

Read off the engine rather than kept as a second copy. Each answer,
follow-up answer and photo measurement is put through every rule on its
own, and whatever fires is what the table shows. So the table can't drift
from what ranking does, and tests/test_rule_map.py fails the day a rule is
added that no single answer or measurement reaches.
"""

from dataclasses import dataclass, field
from functools import lru_cache

from app.domains.causes.vocabulary import load_causes
from app.domains.intake.followups import FOLLOWUPS, FollowUp
from app.domains.intake.spec import QUESTIONS, Question
from app.domains.ranking.pass1 import PRIOR
from app.domains.ranking.rules import CAUSE_RULES, CauseRule
from app.domains.ranking.service import CHECK_CONFIRMS_LOGIT, CHECK_RULES_OUT_LOGIT


@dataclass(frozen=True)
class Measurement:
    """One photo signal, probed twice: just past normal and at full
    strength. Signal rules ramp with the reading, so a single number would
    misstate them."""

    id: str
    label: str
    help: str
    mild: dict[str, float]
    mild_text: str
    strong: dict[str, float]
    strong_text: str
    excludes: tuple[str, ...] = ()
    """Measurements that can't both count: when the small-then-big pattern
    beats chance, missing dots are carryover's, not a blockage's."""


MEASUREMENTS = [
    Measurement(
        "size_cv", "Size varies shot to shot", "the spread of deposit sizes, against a 0.15 spec limit",
        {"size_cv": 0.20}, "a spread of 0.20", {"size_cv": 0.45}, "0.45 or more",
    ),
    Measurement(
        "small_then_big", "A small dot, then an oversized one",
        "in dispense order, more often than chance would give (p < 0.05)",
        {"small_then_big_count": 3, "small_then_big_chance_p": 0.049}, "p just under 0.05",
        {"small_then_big_count": 3, "small_then_big_chance_p": 0.001}, "p near 0",
        excludes=("missing_count",),
    ),
    Measurement(
        "missing_count", "Missing deposits, without that pattern",
        "nothing at a recipe position, and no small-then-big pattern to explain it",
        {"missing_count": 1}, "1 missing", {"missing_count": 5}, "5 or more",
        excludes=("small_then_big",),
    ),
    Measurement(
        "irregular_count", "Irregular deposits", "a distorted outline: circularity below 0.80",
        {"irregular_count": 1}, "1 deposit", {"irregular_count": 5}, "5 or more",
    ),
]

QUESTION_TITLES = {
    "signature": "Q1 · What it looks like",
    "trajectory": "Q2 · How it behaves",
    "footprint": "Q3 · What it follows",
    "inputs": "Q4 · Material and supply",
    "response": "Q5 · What helps",
}
QUESTION_NOTES = {
    "signature": "The photo usually answers this one, and its measurements carry the evidence.",
    "inputs": "Pick as many as apply.",
}
FOLLOWUP_TITLES = {
    "recent_change": "Follow-up · What changed",
    "location": "Follow-up · Where on the board",
    "next_dot": "Follow-up · The dot after a small one",
    "pressure_gauge": "Follow-up · Pressure gauge",
}


@dataclass
class Cell:
    cause_id: str
    weight: float
    label: str
    detail: str
    source: str
    weight_mild: float | None = None


@dataclass
class Row:
    id: str
    label: str
    help: str
    cells: list[Cell]
    mild_text: str | None = None
    strong_text: str | None = None
    excludes: list[str] = field(default_factory=list)


@dataclass
class Group:
    id: str
    kind: str  # "measured" | "question" | "followup"
    title: str
    prompt: str
    note: str
    single: bool
    rows: list[Row]


@dataclass
class CauseColumn:
    cause_id: str
    label: str
    rule_count: int


@dataclass
class RuleMap:
    prior: float
    rule_count: int
    check_confirms: float
    check_rules_out: float
    causes: list[CauseColumn]
    groups: list[Group]


EMPTY_FINGERPRINT: dict = {"axes": {}, "signals": {}, "followups": {}}

Hits = dict[tuple[str, int], tuple[float, CauseRule]]


def fires(fingerprint: dict) -> Hits:
    """Every rule that fires on this fingerprint, keyed by (cause, position)."""
    hits: Hits = {}
    for cause_id, rules in CAUSE_RULES.items():
        for i, rule in enumerate(rules):
            weight = rule.evaluate(fingerprint)
            if weight is not None:
                hits[(cause_id, i)] = (weight, rule)
    return hits


def _cells(hits: Hits, mild: Hits | None = None) -> list[Cell]:
    cells = []
    for key, (weight, rule) in hits.items():
        mild_hit = (mild or {}).get(key)
        cells.append(
            Cell(
                cause_id=key[0], weight=round(weight, 4), label=rule.label, detail=rule.detail,
                source=rule.source, weight_mild=round(mild_hit[0], 4) if mild_hit else None,
            )
        )
    return cells


def _measured_group() -> Group:
    rows = [
        Row(
            id=f"photo:{m.id}", label=m.label, help=m.help,
            cells=_cells(
                fires({**EMPTY_FINGERPRINT, "signals": m.strong}),
                mild=fires({**EMPTY_FINGERPRINT, "signals": m.mild}),
            ),
            mild_text=m.mild_text, strong_text=m.strong_text,
            excludes=[f"photo:{other}" for other in m.excludes],
        )
        for m in MEASUREMENTS
    ]
    return Group(
        id="photo", kind="measured", title="From the photo",
        prompt="Measured on every deposit, against the recipe",
        note="These grow with the reading. Each cell shows full strength.",
        single=False, rows=rows,
    )


def _question_group(question: Question) -> Group:
    def answered(value: str) -> dict:
        answer = [value] if question.kind == "multi" else value
        return {**EMPTY_FINGERPRINT, "axes": {question.axis: answer}}

    rows = [
        Row(id=f"{question.id}:{o.value}", label=o.label, help=o.help_text, cells=_cells(fires(answered(o.value))))
        for o in question.options
    ]
    return Group(
        id=question.id, kind="question", title=QUESTION_TITLES.get(question.id, question.id),
        prompt=question.prompt, note=QUESTION_NOTES.get(question.id, ""),
        single=question.kind == "single", rows=rows,
    )


def _followup_group(followup: FollowUp) -> Group:
    q = followup.question
    rows = [
        Row(
            id=f"followup:{q.id}:{o.value}", label=o.label, help=o.help_text,
            cells=_cells(fires({**EMPTY_FINGERPRINT, "followups": {q.id: o.value}})),
        )
        for o in q.options
    ]
    return Group(
        id=f"followup:{q.id}", kind="followup", title=FOLLOWUP_TITLES.get(q.id, q.id),
        prompt=q.prompt, note=followup.asked_when, single=True, rows=rows,
    )


@lru_cache
def rule_map() -> RuleMap:
    return RuleMap(
        prior=PRIOR,
        rule_count=sum(len(rules) for rules in CAUSE_RULES.values()),
        check_confirms=CHECK_CONFIRMS_LOGIT,
        check_rules_out=CHECK_RULES_OUT_LOGIT,
        causes=[
            CauseColumn(cause_id=c["id"], label=c["label"], rule_count=len(CAUSE_RULES.get(c["id"], [])))
            for c in load_causes()
        ],
        groups=[
            _measured_group(),
            *(_question_group(q) for q in QUESTIONS),
            *(_followup_group(f) for f in FOLLOWUPS),
        ],
    )
