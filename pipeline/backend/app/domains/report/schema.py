from pydantic import BaseModel

from app.domains.ranking.schema import BackingOut


class QualityAspectOut(BaseModel):
    key: str
    label: str
    stars: int
    passed: int
    total: int
    detail: str


class DispensingQualityOut(BaseModel):
    """Bonus 2: how good the deposits in the photo are. Rates the
    dispensing, not the diagnosis."""

    aspects: list[QualityAspectOut]
    overall: int
    passed: int
    total: int
    detail: str


class DefectOut(BaseModel):
    signature: list[str]
    magnitude: str
    dispensing_quality: DispensingQualityOut | None = None


class QualityOut(BaseModel):
    ok: bool | None
    reason: str | None


class CheckLogRowOut(BaseModel):
    sequence: int
    check_name: str
    cause_id: str | None
    outcome: str | None
    result_detail: str | None


class RecommendedActionOut(BaseModel):
    """What to check next, in order. Distinct from `check_log`, which is
    what was already done — the report used to carry only the latter."""

    step: int
    check_name: str
    cause_id: str
    cause_label: str
    is_change: bool
    help: str
    likelihood: float | None


class CauseTallyOut(BaseModel):
    cause_id: str
    label: str
    count: int
    share: float


class PrecedentsOut(BaseModel):
    total: int
    diagnosed_total: int
    matched_axes: list[str]
    by_cause: list[CauseTallyOut]
    sentence: str | None
    note: str


class ReportOut(BaseModel):
    case_id: int
    complaint: str | None
    complaint_text: str | None
    defect: DefectOut
    quality: QualityOut
    tier: str | None
    tier_reason: str | None = None
    backing: BackingOut | None = None
    """What backs the top cause, counted from its evidence."""
    disagreement_note: str | None
    causes: list[dict]
    explanation: str | None
    explanation_used_llm: bool
    recommended_actions: list[RecommendedActionOut]
    precedents: PrecedentsOut | None
    check_log: list[CheckLogRowOut]
    diagnosis: dict | None
    verification: dict | None
    engineer_notes: str | None
    rules_version: str
    llm_used: bool
    disclaimer: str
    action_count: int
    resolved: bool
    close_tier: str | None


class CloseCaseResponse(BaseModel):
    tier: str
    gaps: list[str]
