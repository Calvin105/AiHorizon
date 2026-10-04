import base64
from dataclasses import asdict

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.cases import crud as cases_crud
from app.domains.cases.fingerprint import with_measurement
from app.domains.vision.magnitude import parse_spec_limit
from app.domains.vision.schema import VisionResultOut
from app.domains.vision.service import run_vision

router = APIRouter(prefix="/cases/{case_id}/vision", tags=["Vision (step 3)"])


@router.post(
    "",
    response_model=VisionResultOut,
    summary="Analyse a dispense photo",
    description=(
        "Runs vision/detect/ against the uploaded photo using this case's own "
        "profile geometry as the expected layout. Quality gate first: an "
        "unmeasurable image reports why and leaves the fingerprint's signals "
        "empty rather than feeding both ranking passes a false measurement. "
        "The latest photo wins: its signals replace the previous photo's, and "
        "the image-only carryover signature is set only while this photo "
        "shows the pattern above chance."
    ),
)
async def analyse_photo(
    case_id: int, photo: UploadFile = File(...), db: Session = Depends(get_db)
) -> VisionResultOut:
    case = cases_crud.get_case(db, case_id)
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Case {case_id} not found")

    raw = await photo.read()
    limit = parse_spec_limit(case.profile.spec_limit, case.profile.spec_metric)
    result = run_vision(raw, case.profile.geometry, limit)

    case.fingerprint = with_measurement(case.fingerprint, result.signals, result.small_then_big_above_chance)
    case.vision_result = {
        "quality_ok": result.quality_ok,
        "quality_reason": result.quality_reason,
        "magnitude": result.magnitude,
        "size_cv_limit": result.size_cv_limit,
        # Kept so a reload mid-interview can still open axis 1 pre-filled
        # rather than losing what the photo already answered.
        "suggested_signature": result.suggested_signature,
        "cv_output": result.cv_output,
        "annotated_image": result.annotated_image,
        "dispensing_quality": result.dispensing_quality,
    }
    db.commit()

    return VisionResultOut(**{k: v for k, v in asdict(result).items() if k in VisionResultOut.model_fields})


@router.get(
    "/annotated-image",
    summary="Retrieve the annotated measurement image",
    description="Returns the annotated PNG image bytes for this case's vision measurement.",
    responses={200: {"content": {"image/png": {}}}},
)
def get_annotated_image(case_id: int, db: Session = Depends(get_db)) -> Response:
    case = cases_crud.get_case(db, case_id)
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Case {case_id} not found")

    annotated = (case.vision_result or {}).get("annotated_image")
    if not annotated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No annotated image found for case {case_id}")

    if annotated.startswith("data:"):
        _, b64 = annotated.split(",", 1)
        raw_png = base64.b64decode(b64)
    else:
        raw_png = base64.b64decode(annotated)

    return Response(content=raw_png, media_type="image/png")

