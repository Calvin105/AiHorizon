"""Step 5's tier table, from DESIGN.md, plus the one route it was missing:

| Tier | Reached when | Shown |
| T1 | A check on this case confirmed the top cause — or: passes agree, signal beats chance, confirmed precedent | One lead cause |
| T2 | Passes agree, no precedent or signal at chance | One lead cause, provisional |
| T3 | Passes disagree, signal beats chance | Both candidates, measurement holds top slot |
| T4 | Passes disagree, signal at chance | No lead cause — show the deciding check instead |

Without a Groq key, pass 2 never runs — "the whole app works with no API
key" (DESIGN.md's opening line), so a missing pass 2 counts as agreement
rather than blocking T1/T2 entirely.

The check route: the gates judge how far a *reading* of the evidence can be
trusted. A check is not a reading. It tests the cause on the machine, and
its result already dominates the likelihood (ranking/service.py), so a
cause confirmed by one used to sit at 99% with the tier still at T2, or at
T4 when the critic had read the complaint differently.
"""

from app.domains.ranking.gates import GateAResult, GateBResult


def passes_agree(pass1_top_id: str, pass2_top_id: str | None) -> bool:
    """`None` covers both "never ran" and "ran but abstained" (see
    pass2.critic_verdict) — read this as *not contradicted* rather than
    *actively agreed*, which is why agreement alone still can't reach T1.
    Only a critic with a real pick is allowed to veto."""
    return pass2_top_id is None or pass1_top_id == pass2_top_id


def _has_confirmed_precedent(gate_b: GateBResult) -> bool:
    return gate_b.matched_count >= 3 and gate_b.contradicting_count == 0


def compute_tier(agree: bool, gate_a: GateAResult, gate_b: GateBResult, *, check_confirmed: bool = False) -> str:
    """`check_confirmed`: a check on this case confirmed the top cause, and
    no check confirmed a different one."""
    if check_confirmed:
        return "T1"
    above_chance = bool(gate_a.above_chance)
    if agree:
        return "T1" if above_chance and _has_confirmed_precedent(gate_b) else "T2"
    return "T3" if above_chance else "T4"


def tier_reason(
    tier: str, *, top_label: str, critic_label: str | None, gate_a: GateAResult, gate_b: GateBResult,
    check_confirmed: bool,
) -> str:
    """Why the ranking sits at this tier, in one or two sentences. The tier
    is the confidence the app shows, so it has to say what it rests on."""
    top = top_label.lower()
    backed = bool(gate_a.above_chance) and _has_confirmed_precedent(gate_b)
    if check_confirmed:
        if critic_label:
            also = (
                f" The second read picked {critic_label.lower()} from the complaint, but a test on the "
                "machine outweighs a reading of the words."
            )
        elif backed:
            also = (
                f" The measured pattern beats chance and {gate_b.matched_count} matching confirmed "
                "cases agree, too."
            )
        else:
            also = ""
        return f"A check on this case confirmed {top}.{also}"
    if tier == "T1":
        return (
            f"The two reads agree, the measured pattern beats chance, and {gate_b.matched_count} "
            f"matching confirmed cases were {top} too."
        )
    if tier == "T2":
        missing = []
        if not gate_a.above_chance:
            missing.append(
                "no measurement singles it out from the other causes"
                if gate_a.deciding_signal else "nothing measured in a photo backs it"
            )
        if not _has_confirmed_precedent(gate_b):
            missing.append(
                f"{gate_b.contradicting_count} of {gate_b.matched_count} matching confirmed cases were "
                "something else" if gate_b.contradicting_count
                else "fewer than 3 matching confirmed cases back it"
            )
        return f"Provisional: {' and '.join(missing)}. A check that confirms it would settle it."
    critic = critic_label.lower() if critic_label else "a different cause"
    if tier == "T3":
        return f"The second read picked {critic}, but the measured pattern still puts {top} on top."
    return (
        f"The second read picked {critic}, and nothing measured separates the two. "
        "A check on either one will settle it."
    )
