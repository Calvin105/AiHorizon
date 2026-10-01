from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.cases import crud as cases_crud
from app.domains.intake import mapper
from app.domains.intake.followups import FOLLOWUPS, next_followup
from app.domains.intake.schema import (
    FollowUpPreviewOut,
    MapFreeTextRequest,
    MapFreeTextResponse,
    NextFollowUpOut,
    QuestionOptionOut,
    QuestionOut,
)
from app.domains.intake.spec import QUESTIONS, Question

router = APIRouter(prefix="/intake", tags=["Intake (steps 1-2)"])


@router.get(
    "/spec",
    response_model=list[QuestionOut],
    summary="Get the question spine",
    description=(
        "The fixed five axes (plus the signature picker, which doubles as axis 1) "
        "that step 1-2 always asks, in DESIGN.md W3's order. Static — no case needed."
    ),
)
def get_spec() -> list[QuestionOut]:
    return [_question_out(q) for q in QUESTIONS]


def _question_out(q: Question) -> QuestionOut:
    return QuestionOut(
        id=q.id, axis=q.axis, prompt=q.prompt, kind=q.kind,
        options=[
            QuestionOptionOut(value=o.value, label=o.label, help_text=o.help_text, exclusive=o.exclusive)
            for o in q.options
        ],
        max_picks=q.max_picks, has_dont_know=q.has_dont_know, has_other=q.has_other,
    )


@router.get(
    "/followups",
    response_model=list[QuestionOut],
    summary="Every adaptive follow-up question",
    description="The bank the next-follow-up endpoint picks from — so a resumed case can label "
    "the follow-up answers already on file. Static — no case needed.",
)
def get_followups() -> list[QuestionOut]:
    return [_question_out(f.question) for f in FOLLOWUPS]


@router.get(
    "/followups/next",
    response_model=NextFollowUpOut | None,
    summary="The follow-up worth asking next, if any",
    description="Runs every answer to every applicable follow-up through the rule engine and "
    "returns the question whose answers would move this case's ranking most, with the reason. "
    "Null once two have been asked, or when no answer would move any cause by ten points.",
)
def get_next_followup(case_id: int, db: Session = Depends(get_db)) -> NextFollowUpOut | None:
    case = cases_crud.get_case(db, case_id)
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Case {case_id} not found")
    found = next_followup(case.fingerprint or {"axes": {}, "signals": {}})
    if found is None:
        return None
    return NextFollowUpOut(
        question=_question_out(found.question),
        reason=found.reason,
        previews=[
            FollowUpPreviewOut(
                value=p.value, label=p.label, top_cause_id=p.top_cause_id,
                top_label=p.top_label, top_likelihood=p.top_likelihood,
            )
            for p in found.previews
        ],
    )


@router.post(
    "/map",
    response_model=MapFreeTextResponse,
    summary="Map free text onto a fixed option (W7 call-1)",
    description=(
        "For the 'Other / describe' path. Maps onto an existing option value only — "
        "never invents one. mapped_value is null if the model can't place it, or no "
        "LLM is configured; the caller should then keep the raw text and mark the "
        "axis unmapped rather than guess. Records the call against the case's W7 budget."
    ),
)
def map_free_text(payload: MapFreeTextRequest, db: Session = Depends(get_db)) -> MapFreeTextResponse:
    case = cases_crud.get_case(db, payload.case_id)
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Case {payload.case_id} not found")

    mapped_value, used_llm = mapper.map_free_text(payload.question_id, payload.text)
    if used_llm:
        case.llm_map_used = True
        db.commit()
    return MapFreeTextResponse(mapped_value=mapped_value, used_llm=used_llm)
