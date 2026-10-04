"""Step 7: report and verify. Compiles what's already on the case — no
new computation except the counts it reads off the measurement and the
evidence, and the optional LLM explanation — into the one view DESIGN.md
W9 specifies: description, identified defect with its dispensing quality
score, the tier and what backs it, causes with evidence and sources, the
check log, confirmed fix, engineer notes, rules version, whether the LLM
was used, and the fixed disclaimer."""

from sqlalchemy.orm import Session

from app.domains.cases.model import Case
from app.domains.checks.suggestions import recommended_actions
from app.domains.ranking.backing import backing
from app.domains.report.explain import write_explanation
from app.domains.retrieval.precedents import precedent_stats
from app.domains.vision.dispensing_quality import rate_dispensing

DISCLAIMER = "Preliminary triage aid, not a replacement for an engineer."


def compile_report(
    case: Case, *, use_llm_explanation: bool, db: Session | None = None
) -> tuple[dict, bool]:
    ranking = case.ranking or {}
    pass1 = ranking.get("pass1", [])
    top3 = pass1[:3]

    # Whatever was written for this case before wins: the budget allows one
    # call, so a re-read has to show the stored analysis rather than an
    # empty section (and must not try to spend the call again).
    explanation, explanation_used_llm = case.explanation, case.explanation_used_llm
    if explanation is None and top3 and use_llm_explanation and not case.llm_explain_used:
        explanation, explanation_used_llm = write_explanation(top3)

    vision = case.vision_result or {}
    fingerprint = case.fingerprint or {"axes": {}, "signals": {}}

    # What to check next, minus whatever has already been checked — the
    # loop log below says what was done, and repeating it back as advice
    # would be a report that stopped reading the case.
    already_done = {cr.check_name for cr in case.check_results}
    actions = recommended_actions(pass1, already_done)

    # Needs a session, so a caller that has none (tests, or any path that
    # only wants the case's own fields) gets a report without the history
    # rather than an error.
    precedents = None
    if db is not None:
        stats = precedent_stats(db, case)
        precedents = {
            "total": stats.total,
            "diagnosed_total": stats.diagnosed_total,
            "matched_axes": stats.matched_axes,
            "by_cause": [
                {"cause_id": t.cause_id, "label": t.label, "count": t.count, "share": t.share}
                for t in stats.by_cause
            ],
            "sentence": stats.sentence,
            "note": stats.note,
        }

    disagreement_note = None
    if ranking.get("tier") in ("T3", "T4"):
        gate_a = ranking.get("gate_a", {})
        disagreement_note = (
            f"Pass 1 (instrument) and pass 2 (critic) disagree on the top cause. {gate_a.get('note', '')}"
        )

    return {
        "case_id": case.case_id,
        "complaint": case.complaint,
        "complaint_text": case.complaint_text,
        "defect": {
            "signature": fingerprint.get("axes", {}).get("signature", []),
            "magnitude": vision.get("magnitude", "unknown"),
            # Rated from the stored measurement rather than read back, so a
            # case measured before the score existed has one too.
            "dispensing_quality": (
                rate_dispensing(vision["cv_output"]) if vision.get("quality_ok") and vision.get("cv_output") else None
            ),
        },
        "quality": {
            "ok": vision.get("quality_ok"),
            "reason": vision.get("quality_reason"),
        },
        "tier": ranking.get("tier"),
        "tier_reason": ranking.get("tier_reason") or None,
        # Counted from the stored evidence, so a ranking from before the
        # count existed reads the same as a fresh one.
        "backing": backing(pass1[0]["evidence"]) if pass1 else None,
        "disagreement_note": disagreement_note,
        "causes": top3,
        "explanation": explanation,
        "explanation_used_llm": explanation_used_llm,
        "recommended_actions": actions,
        "precedents": precedents,
        "check_log": [
            {
                "sequence": cr.sequence, "check_name": cr.check_name, "cause_id": cr.cause_id,
                "outcome": cr.outcome.value if cr.outcome else None, "result_detail": cr.result_detail,
            }
            for cr in case.check_results
        ],
        "diagnosis": case.diagnosis,
        "verification": case.verification,
        "engineer_notes": case.engineer_notes,
        "rules_version": case.rules_version,
        "llm_used": case.llm_map_used or case.llm_critic_used or case.llm_explain_used or explanation_used_llm,
        "disclaimer": DISCLAIMER,
        "action_count": case.action_count,
        "resolved": case.resolved,
        "close_tier": case.tier.value if case.tier else None,
    }, explanation_used_llm
