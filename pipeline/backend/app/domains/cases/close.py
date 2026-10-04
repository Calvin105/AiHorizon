"""Step 8: close case. DESIGN.md's five conditions:

- a check confirmed the cause
- exactly one thing was changed — and it was aimed at that cause
- the deciding signal was re-measured, against a measurement from before
- it came back inside spec
- it held for the next N shots

All five -> CONFIRMED. None -> UNVERIFIED. Anything in between ->
PLAUSIBLE, shown as context but adjusting nothing.

`action_count` counts changes only, never observations — see
CheckResult.is_change. Running five checks to narrow the cause down and
then changing one thing is the behaviour this tier is meant to reward,
not to disqualify.

Each condition is read off the check log itself rather than the case's
`diagnosis` summary, because the log is what the claim rests on. Two
things the summary could not see now block CONFIRMED: checks that confirm
*different* causes, and a single change aimed at a cause other than the
confirmed one. Either way "the symptom went away" cannot be credited to
the cause the record would name.
"""

from dataclasses import dataclass

from app.domains.cases.model import Case
from app.domains.causes.vocabulary import get_cause
from app.domains.enums import CaseTier, CheckOutcome

MIN_SHOTS_HELD = 20
CONDITION_COUNT = 5

#: The re-measured signals in the words the gaps are read in.
SIGNAL_WORDS = {
    "size_cv": "size spread",
    "missing_count": "missing deposits",
    "irregular_count": "irregular deposits",
    "small_then_big_chance_p": "small-then-big pattern",
}


@dataclass
class CloseResult:
    tier: CaseTier
    gaps: list[str]


def _label(cause_id: str | None) -> str:
    cause = get_cause(cause_id) if cause_id else None
    return cause["label"].lower() if cause else (cause_id or "no cause").replace("_", " ")


def confirmed_cause(case: Case) -> tuple[str | None, str | None]:
    """(the one cause the checks confirmed, or None; the gap if there isn't one)."""
    confirmed = {c.cause_id for c in case.check_results if c.outcome == CheckOutcome.CONFIRMS and c.cause_id}
    ruled_out = {c.cause_id for c in case.check_results if c.outcome == CheckOutcome.RULES_OUT and c.cause_id}
    if not confirmed:
        return None, "no check confirmed the cause"
    if len(confirmed) > 1:
        names = " and ".join(sorted(_label(c) for c in confirmed))
        return None, f"checks confirmed different causes ({names}) — the record can't say which one it was"
    cause_id = next(iter(confirmed))
    if cause_id in ruled_out:
        return None, f"{_label(cause_id)} was both confirmed and ruled out by checks"
    return cause_id, None


def close_case(case: Case) -> CloseResult:
    verification = case.verification or {}
    gaps: list[str] = []

    # 1. a check confirmed the cause
    cause_id, cause_gap = confirmed_cause(case)
    if cause_gap:
        gaps.append(cause_gap)

    # 2. exactly one thing was changed, aimed at that cause
    changes = [c for c in case.check_results if c.is_change]
    if not changes:
        gaps.append("nothing was changed, so no fix was applied or tested")
    elif len(changes) > 1:
        gaps.append(f"{len(changes)} things changed at once — no way to say which one worked")
    elif cause_id and changes[0].cause_id != cause_id:
        gaps.append(
            f"the one change was aimed at {_label(changes[0].cause_id)}, not the confirmed cause "
            f"({_label(cause_id)}) — the fix can't be credited to it"
        )

    # 3. the deciding signal was re-measured, against a measurement from before
    if not verification:
        gaps.append("the deciding signal was never re-measured")
    elif verification.get("after") is None:
        gaps.append("the verification photo couldn't be measured — retake it")
    elif verification.get("before") is None:
        gaps.append(
            "there was no measurement from before the change, so the re-measurement has "
            "nothing to show it improved on"
        )

    # 4. it came back inside spec
    if not verification.get("in_spec"):
        failed = [SIGNAL_WORDS.get(c["signal"], c["signal"]) for c in verification.get("checks", []) if not c.get("ok")]
        detail = f" ({', '.join(failed)} still out)" if failed and verification.get("after") is not None else ""
        gaps.append(f"re-measurement did not come back in spec{detail}")

    # 5. it held for the next N shots
    shots = verification.get("shots_measured")
    if not shots or shots < MIN_SHOTS_HELD:
        gaps.append(f"held for {shots or 0} shots, short of the {MIN_SHOTS_HELD}-shot bar")

    if not gaps:
        tier = CaseTier.CONFIRMED
    elif len(gaps) == CONDITION_COUNT:
        tier = CaseTier.UNVERIFIED
    else:
        tier = CaseTier.PLAUSIBLE

    return CloseResult(tier=tier, gaps=gaps)
