"""The rule table on the home page: every answer and measurement the rule
engine knows, against every cause it moves, with the weight and the page.

Read off the engine rather than kept as a second copy. Each answer,
follow-up answer and photo measurement is put through every rule on its
own, and whatever fires is what the table shows. So the table can't drift
from what ranking does, and tests/test_rule_map.py fails the day a rule is
added that no single answer or measurement reaches.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime

from app.domains.causes.vocabulary import load_causes
from app.domains.intake.followups import FOLLOWUPS, FollowUp
from app.domains.intake.spec import QUESTIONS, Question
from app.domains.ranking.model import RuleOverride
from app.domains.ranking.pass1 import PRIOR
from app.domains.ranking.rules import CAUSE_RULES, CauseRule
from app.domains.ranking.service import CHECK_CONFIRMS_LOGIT, CHECK_RULES_OUT_LOGIT
from app.domains.ranking.weights import edited_weight, rule_key, weigh


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
    rule_key: str
    weight: float
    """At the weight in force; 0 when an engineer switched the rule off."""
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
class RuleInfo:
    """One rule, for the rules page's list."""

    key: str
    cause_id: str
    label: str
    detail: str
    source: str
    kind: str
    manual_weight: float
    """The weight in rules.py, from the NPL guide or the NSW brief."""
    weight: float
    """The weight in force: the manual's, unless an engineer changed it."""
    full_strength: float | None
    """Signal rules only: what it adds at its strongest reading."""
    triggers: list[str]
    """The ids of the table rows that fire it."""
    note: str | None = None
    updated_at: datetime | None = None


@dataclass
class RuleMap:
    prior: float
    rule_count: int
    check_confirms: float
    check_rules_out: float
    causes: list[CauseColumn]
    groups: list[Group]
    rules: list[RuleInfo]


EMPTY_FINGERPRINT: dict = {"axes": {}, "signals": {}, "followups": {}}

Hits = dict[tuple[str, int], tuple[float, CauseRule]]


def fires(fingerprint: dict) -> Hits:
    """Every rule whose test passes on this fingerprint, keyed by (cause,
    position), with its contribution at the weight in force. A rule an
    engineer switched off still passes its test, so it keeps its place in
    the table, at 0."""
    hits: Hits = {}
    for cause_id, rules in CAUSE_RULES.items():
        for i, rule in enumerate(rules):
            if rule.evaluate(fingerprint) is not None:
                hits[(cause_id, i)] = (weigh(cause_id, rule, fingerprint) or 0.0, rule)
    return hits


def _cells(hits: Hits, mild: Hits | None = None) -> list[Cell]:
    cells = []
    for key, (weight, rule) in hits.items():
        mild_hit = (mild or {}).get(key)
        cells.append(
            Cell(
                cause_id=key[0], rule_key=rule_key(key[0], rule), weight=round(weight, 4), label=rule.label,
                detail=rule.detail, source=rule.source,
                weight_mild=round(mild_hit[0], 4) if mild_hit else None,
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


def _rules(groups: list[Group], edits: Mapping[str, RuleOverride]) -> list[RuleInfo]:
    triggers: dict[str, list[str]] = {}
    full_strength: dict[str, float] = {}
    for group in groups:
        for row in group.rows:
            for cell in row.cells:
                triggers.setdefault(cell.rule_key, []).append(row.id)
                if group.kind == "measured":
                    full_strength[cell.rule_key] = cell.weight

    out = []
    for cause_id, rules in CAUSE_RULES.items():
        for rule in rules:
            key = rule_key(cause_id, rule)
            edit = edits.get(key)
            weight = edited_weight(key)
            out.append(
                RuleInfo(
                    key=key, cause_id=cause_id, label=rule.label, detail=rule.detail, source=rule.source,
                    kind=rule.kind, manual_weight=rule.evaluate.weight,
                    weight=rule.evaluate.weight if weight is None else weight,
                    full_strength=full_strength.get(key), triggers=triggers.get(key, []),
                    note=edit.note if edit else None, updated_at=edit.updated_at if edit else None,
                )
            )
    return out


def rule_map(edits: Mapping[str, RuleOverride] | None = None) -> RuleMap:
    """`edits` are the saved overrides, for their notes; the weights in
    force come from ranking/weights.py, as ranking reads them."""
    groups = [
        _measured_group(),
        *(_question_group(q) for q in QUESTIONS),
        *(_followup_group(f) for f in FOLLOWUPS),
    ]
    return RuleMap(
        prior=PRIOR,
        rule_count=sum(len(rules) for rules in CAUSE_RULES.values()),
        check_confirms=CHECK_CONFIRMS_LOGIT,
        check_rules_out=CHECK_RULES_OUT_LOGIT,
        causes=[
            CauseColumn(cause_id=c["id"], label=c["label"], rule_count=len(CAUSE_RULES.get(c["id"], [])))
            for c in load_causes()
        ],
        groups=groups,
        rules=_rules(groups, edits or {}),
    )
