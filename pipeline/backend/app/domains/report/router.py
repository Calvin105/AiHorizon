from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.cases import crud as cases_crud
from app.domains.cases.close import close_case, confirmed_cause
from app.domains.enums import CaseTier
from app.domains.report.schema import CloseCaseResponse, ReportOut
from app.domains.report.service import compile_report
from app.domains.report.verify import build_verification
from app.domains.vision.magnitude import parse_spec_limit
from app.domains.vision.service import run_vision

router = APIRouter(prefix="/cases/{case_id}", tags=["Report & close (steps 7-8)"])


def _get_case_or_404(db: Session, case_id: int):
    case = cases_crud.get_case(db, case_id)
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Case {case_id} not found")
    return case


@router.get(
    "/report", response_model=ReportOut, summary="Compile the step-7 report",
    description="Original description, defect + stars, quality, causes with evidence, check log, "
    "confirmed fix, rules version, whether the LLM was used, and the fixed disclaimer.",
)
def get_report(case_id: int, use_llm_explanation: bool = True, db: Session = Depends(get_db)) -> ReportOut:
    case = _get_case_or_404(db, case_id)
    report, used_llm = compile_report(case, use_llm_explanation=use_llm_explanation, db=db)
    if used_llm:
        case.llm_explain_used = True
        # Persisted here rather than regenerated on the next read — see the
        # explanation column on Case.
        case.explanation = report["explanation"]
        case.explanation_used_llm = True
        db.commit()
    return ReportOut(**report)


@router.post(
    "/verify",
    summary="Re-measure the deciding signal (step 7's one-tap verify)",
    description="Upload a fresh photo after the fix. Re-runs the same measurement as step 3 and "
    "checks it against everything a photo can show — size spread within the profile's limit, "
    "nothing missing, no irregular deposits, no carryover pattern — then reports the signal that "
    "was out of spec before. `shots_measured` is the operator's report of how long the fix held; "
    "a photo cannot see that, so it is recorded as theirs.",
)
async def verify(
    case_id: int,
    photo: UploadFile = File(...),
    shots_measured: int | None = Form(None),
    db: Session = Depends(get_db),
) -> dict:
    case = _get_case_or_404(db, case_id)
    before = (case.fingerprint or {}).get("signals") or {}

    raw = await photo.read()
    limit = parse_spec_limit(case.profile.spec_limit, case.profile.spec_metric)
    result = run_vision(raw, case.profile.geometry, limit)
    dots = result.cv_output.get("dots", []) if result.quality_ok else []

    cause_id, _ = confirmed_cause(case)
    verification = build_verification(
        before, result.signals if result.quality_ok else None, limit,
        cause_id or (case.ranking or {}).get("top_cause_id"),
        deposits_measured=sum(1 for d in dots if d.get("area_ratio") is not None) if dots else None,
        shots_reported=shots_measured,
    )
    case.verification = verification
    db.commit()
    return verification


@router.post(
    "/close", response_model=CloseCaseResponse, summary="Close the case (step 8)",
    description="Applies the five-condition CONFIRMED rule. Never promotes ranking on its own — "
    "a CONFIRMED case only feeds Gate B the next time some other case runs step 5b.",
)
def close(case_id: int, db: Session = Depends(get_db)) -> CloseCaseResponse:
    case = _get_case_or_404(db, case_id)
    result = close_case(case)
    case.tier = result.tier
    case.resolved = result.tier == CaseTier.CONFIRMED
    case.closed_at = datetime.now(UTC)
    db.commit()
    return CloseCaseResponse(tier=result.tier.value, gaps=result.gaps)
