"""Two suggested checks per cause: something to *look at*, and something to
*change*. The remedies are the "Response: X helps" actions already cited in
ranking/rules.py; the observations are the cheap, reversible way to test the
same cause without spending the case's one change.

Offering only the remedy would make the loop's own advice "change something,
then tell us if the symptom went away", which is the post-hoc credit
assignment DESIGN.md's step 8 exists to keep out of the database.

Per DESIGN.md W4, never invent a parameter number — pressure/time gets the
"small steps, engineer to confirm" phrasing instead of a figure.

This list lived in the wizard's page.tsx and was unreachable from the
report, so step 7 could show what had already been done but never what to
do next. It is here so both read the same source; the wizard fetches it
from GET /causes/checks.

Each check also says what result confirms its cause and what rules it out,
so an operator knows what they are looking for before they look, and what
to answer once they have.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SuggestedCheck:
    name: str
    #: Does running this alter the machine, tooling or material? Only
    #: changes count toward ``action_count``, and step 8 can only close
    #: CONFIRMED when exactly one thing was changed.
    is_change: bool
    help: str
    #: What you see when it is this cause, and when it isn't.
    confirms_if: str
    rules_out_if: str


CHECK_SUGGESTIONS: dict[str, list[SuggestedCheck]] = {
    "volume_too_small_carryover": [
        SuggestedCheck(
            "Check the next dot after each small one", False, "is it oversized? that's the carryover signature",
            confirms_if="the dot after each small or missing one comes out oversized",
            rules_out_if="the dot after a small one is normal size",
        ),
        SuggestedCheck(
            "Increase dispense time in small steps within your process spec", True,
            "the NPL guide's fix for big dot / small dot — engineer to confirm the figure",
            confirms_if="the small dots fill out and the oversized ones after them shrink back",
            rules_out_if="nothing changes, or every dot just grows",
        ),
    ],
    "pressure_time_instability": [
        SuggestedCheck(
            "Watch the pressure gauge across 20 shots", False, "look for it wandering, not just the set value",
            confirms_if="the gauge wanders or dips between shots",
            rules_out_if="the gauge holds steady at the set value through every shot",
        ),
        SuggestedCheck(
            "Adjust pressure or shot time in small steps within your process spec", True,
            "engineer to confirm the figure",
            confirms_if="the size stops varying from shot to shot",
            rules_out_if="the size varies as much as before",
        ),
    ],
    "air_in_fluid_path": [
        SuggestedCheck(
            "Hold the syringe up to the light", False, "look for bubbles or a slug in the barrel",
            confirms_if="you see bubbles or an air slug in the barrel",
            rules_out_if="the barrel is full and clear all the way down",
        ),
        SuggestedCheck(
            "Purge the line, or swap in a fresh syringe", True, "changes the material supply",
            confirms_if="the dots come back even",
            rules_out_if="the dots vary just as much afterwards",
        ),
    ],
    "material_rheology_change": [
        SuggestedCheck(
            "Check the lot date and out-time against spec", False, "reading the label costs nothing",
            confirms_if="the lot is new, or past its out-time",
            rules_out_if="it's the lot that ran fine, well inside its out-time",
        ),
        SuggestedCheck(
            "Let the material warm up to spec temperature", True, "changes the material condition",
            confirms_if="the dots settle once the material is at temperature",
            rules_out_if="no difference once it's at temperature",
        ),
    ],
    "nozzle_blockage": [
        SuggestedCheck(
            "Look at the needle tip under a loupe", False, "partial blockage is usually visible",
            confirms_if="dried material, a burr or debris at the tip or in the bore",
            rules_out_if="the tip is clean and the bore is clear",
        ),
        SuggestedCheck(
            "Wipe or change the needle", True, "changes the tooling",
            confirms_if="full, round dots come back with the clean needle",
            rules_out_if="the same defect with a clean needle",
        ),
    ],
    "dispense_height_or_board_bending": [
        SuggestedCheck(
            "Measure standoff at the corners and the centre", False, "a bent board reads differently across it",
            confirms_if="the standoff differs across the board",
            rules_out_if="the standoff is the same everywhere",
        ),
        SuggestedCheck(
            "Re-check dispense height and board clamping", True, "changes the setup",
            confirms_if="the shapes even out once height and clamping are reset",
            rules_out_if="no change after resetting them",
        ),
    ],
    "equipment_condition": [
        SuggestedCheck(
            "Inspect the valve and mounting for wear or residue", False, "look before touching",
            confirms_if="wear, residue or a loose mounting on the valve",
            rules_out_if="the valve and mounting are clean and tight",
        ),
        SuggestedCheck(
            "Restart or re-home the machine", True, "changes the machine state",
            confirms_if="the defect clears after the restart",
            rules_out_if="the defect is still there afterwards",
        ),
    ],
}


def suggestions_for(cause_id: str) -> list[SuggestedCheck]:
    return CHECK_SUGGESTIONS.get(cause_id, [])


def recommended_actions(ranked_causes: list[dict], already_done: set[str]) -> list[dict]:
    """The step-5 "what should I check first" sequence, for the report.

    Ordered by the cause's own likelihood, and within a cause the
    observation comes before the change — the loop can afford any number
    of looks but only one change before CONFIRMED is out of reach, so
    recommending the change first would spend the case's single budget on
    its least certain step.

    Checks already logged on this case are dropped: a report that reopens
    with "check the syringe for bubbles" after the operator has just done
    exactly that is advice that has stopped reading the case.
    """
    actions: list[dict] = []
    for cause in ranked_causes:
        cause_id = cause.get("cause_id")
        if not cause_id:
            continue
        for suggestion in suggestions_for(cause_id):
            if suggestion.name in already_done:
                continue
            actions.append(
                {
                    "step": len(actions) + 1,
                    "check_name": suggestion.name,
                    "cause_id": cause_id,
                    "cause_label": cause.get("label", cause_id),
                    "is_change": suggestion.is_change,
                    "help": suggestion.help,
                    "likelihood": cause.get("likelihood"),
                }
            )
    return actions
