"""Adaptive follow-ups — DESIGN.md W3, and the brief's bonus challenge: "the
AI dynamically asks additional questions depending on the user's answers".

The five spine questions are always asked: they are the retrieval key, and
only work as one because every case answers all five. Follow-ups are chosen
per case and stored apart from the axes, under fingerprint["followups"], so
they feed the ranking but never the case matching — a question asked in one
case and skipped in another can't be compared between them.

Which follow-up, if any, is decided by the same rank_causes() that ranks
the case, not by a model. Every answer to every candidate question is run
through it, and the one asked is the question whose answers would move the
ranking most — flipping the lead first, then the largest swing — with that
reason shown to the operator. At most MAX_FOLLOWUPS, and none at all when
no answer would move any cause by MIN_SWING: a question that can't change
the outcome isn't worth the operator's time.

Two of the four are the brief's own example questions ("Has the material,
nozzle or process setting recently changed?", "Is the defect happening at
one location or across multiple locations?"), asked only where the answers
can matter.
"""

from collections.abc import Callable
from dataclasses import dataclass

from app.domains.intake.spec import Question, QuestionOption
from app.domains.ranking.pass1 import rank_causes

MAX_FOLLOWUPS = 2
MIN_SWING = 0.10
"""An answer has to move some cause's likelihood by ten points or more."""

NO_EVIDENCE_VALUES = frozenset({"nothing_known", "not_checked", "cant_see"})


def _axis(fp: dict, axis: str):
    return (fp.get("axes") or {}).get(axis)


def _signature(fp: dict) -> set[str]:
    return set(_axis(fp, "signature") or [])


@dataclass(frozen=True)
class FollowUp:
    question: Question
    applies: Callable[[dict], bool]
    """Whether the question means anything for this case at all."""


FOLLOWUPS: list[FollowUp] = [
    FollowUp(
        Question(
            id="recent_change", axis="followup", kind="single",
            prompt="It started suddenly — what changed just before it did?",
            options=[
                QuestionOption("new_material", "New material lot or syringe", "a fresh barrel or a new lot went on"),
                QuestionOption("needle_changed", "Needle or nozzle changed", "a different needle, or one re-fitted"),
                QuestionOption("fixture_changed", "Board, fixture or clamping changed", "a new panel, jig or clamp set-up"),
                QuestionOption("program_changed", "Program or settings edited", "dispense time, heights, speeds"),
                QuestionOption("machine_serviced", "Machine serviced or stripped down", "cleaned, repaired or moved"),
                QuestionOption("nothing_known", "Nothing that I know of", "adds no evidence", exclusive=True),
            ],
            has_dont_know=False, has_other=False,
        ),
        # DESIGN.md W3: the one branch where "what changed?" discriminates.
        applies=lambda fp: _axis(fp, "trajectory") == "sudden_step",
    ),
    FollowUp(
        Question(
            id="location", axis="followup", kind="single",
            prompt="Where on the board does it happen?",
            options=[
                QuestionOption("one_area", "One area or one edge", "worse towards a corner or a side"),
                QuestionOption("random_spots", "Random spots, different each board", "no fixed place"),
                QuestionOption("everywhere_same", "Everywhere, about the same", "every position alike"),
            ],
            has_dont_know=False, has_other=False,
        ),
        applies=lambda fp: bool(_signature(fp)),
    ),
    FollowUp(
        Question(
            id="next_dot", axis="followup", kind="single",
            prompt="Right after a small or missing dot, what is the next dot like?",
            options=[
                QuestionOption("oversized", "Bigger than normal", "as if it caught the missing material"),
                QuestionOption("normal", "Normal size", "the next one comes out fine"),
                QuestionOption("not_checked", "Haven't looked", "adds no evidence — the loop can check it"),
            ],
            has_dont_know=False, has_other=False,
        ),
        # The photo answers this itself when it has the dispense order.
        applies=lambda fp: bool(_signature(fp) & {"missing", "too_little", "size_varies"})
        and "small_then_big_chance_p" not in (fp.get("signals") or {}),
    ),
    FollowUp(
        Question(
            id="pressure_gauge", axis="followup", kind="single",
            prompt="Watch the pressure gauge while it dispenses — does it move?",
            options=[
                QuestionOption("wanders", "It wanders or dips during a run", "not just at start-up"),
                QuestionOption("steady", "Steady at the set value", "the needle doesn't move"),
                QuestionOption("cant_see", "Can't see a gauge", "adds no evidence"),
            ],
            has_dont_know=False, has_other=False,
        ),
        applies=lambda fp: "size_varies" in _signature(fp),
    ),
]


def followup_by_id(question_id: str) -> FollowUp | None:
    return next((f for f in FOLLOWUPS if f.question.id == question_id), None)


@dataclass
class Preview:
    value: str
    label: str
    top_cause_id: str
    top_label: str
    top_likelihood: float


@dataclass
class NextFollowUp:
    question: Question
    reason: str
    previews: list[Preview]


def _with_answer(fingerprint: dict, question_id: str, value: str) -> dict:
    return {**fingerprint, "followups": {**(fingerprint.get("followups") or {}), question_id: value}}


def next_followup(fingerprint: dict) -> NextFollowUp | None:
    asked = fingerprint.get("followups") or {}
    if len(asked) >= MAX_FOLLOWUPS:
        return None

    base = rank_causes(fingerprint)
    base_p = {c.cause_id: c.likelihood for c in base}
    base_top = base[0]

    best: tuple[tuple[bool, float], NextFollowUp] | None = None
    for followup in FOLLOWUPS:
        q = followup.question
        if q.id in asked or not followup.applies(fingerprint):
            continue

        previews, strongest = [], (0.0, None, None)  # (swing, option, cause)
        flips = False
        for option in q.options:
            ranked = rank_causes(_with_answer(fingerprint, q.id, option.value))
            top = ranked[0]
            previews.append(Preview(option.value, option.label, top.cause_id, top.label, round(top.likelihood, 4)))
            if option.value in NO_EVIDENCE_VALUES:
                continue
            flips = flips or top.cause_id != base_top.cause_id
            for cause in ranked:
                swing = abs(cause.likelihood - base_p[cause.cause_id])
                if swing > strongest[0]:
                    strongest = (swing, option, cause)

        swing, option, cause = strongest
        if swing < MIN_SWING or option is None or cause is None:
            continue
        before, after = round(base_p[cause.cause_id] * 100), round(cause.likelihood * 100)
        name = cause.label.split(" (")[0].lower()  # the short name, without the parenthetical gloss
        reason = (
            f"Asked because the answer can change the lead: “{option.label}” would put "
            f"{name} at {after}% (now {before}%)."
            if flips
            else f"Asked because “{option.label}” would move {name} from {before}% to {after}%."
        )
        candidate = ((flips, swing), NextFollowUp(question=q, reason=reason, previews=previews))
        if best is None or candidate[0] > best[0]:
            best = candidate

    return None if best is None else best[1]
