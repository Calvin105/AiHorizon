"""Step 8: close case. DESIGN.md's five conditions, verbatim:

- a check confirmed the cause
- exactly one thing was changed
- the deciding signal was re-measured
- it came back inside spec
- it held for the next N shots

All five -> CONFIRMED. Zero -> UNVERIFIED. Anything in between -> PLAUSIBLE,
shown as context but adjusting nothing. `action_count > 1` disqualifying
CONFIRMED outright falls straight out of condition 2 here — it isn't a
separate rule, it's what "exactly one thing was changed" already means.
"""

from dataclasses import dataclass

from app.domains.cases.model import Case
from app.domains.enums import CaseTier

MIN_SHOTS_HELD = 20


@dataclass
class CloseResult:
    tier: CaseTier
    gaps: list[str]


def close_case(case: Case) -> CloseResult:
    diagnosis = case.diagnosis or {}
    verification = case.verification or {}

    gaps: list[str] = []

    if not diagnosis.get("confirmed_by"):
        gaps.append("no check confirmed the cause")

    if case.action_count != 1:
        gaps.append(f"{case.action_count} changes at once, not exactly one — cause never cleanly tested")

    if verification.get("signal") is None or verification.get("after") is None:
        gaps.append("the deciding signal was never re-measured")

    if not verification.get("in_spec"):
        gaps.append("re-measurement did not come back in spec")

    shots = verification.get("shots_measured")
    if not shots or shots < MIN_SHOTS_HELD:
        gaps.append(f"held for {shots or 0} shots, short of the {MIN_SHOTS_HELD}-shot bar")

    if not gaps:
        tier = CaseTier.CONFIRMED
    elif len(gaps) == 5:
        tier = CaseTier.UNVERIFIED
    else:
        tier = CaseTier.PLAUSIBLE

    return CloseResult(tier=tier, gaps=gaps)
