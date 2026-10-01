from pydantic import BaseModel


class QuestionOptionOut(BaseModel):
    value: str
    label: str
    help_text: str
    exclusive: bool


class QuestionOut(BaseModel):
    id: str
    axis: str
    prompt: str
    kind: str
    options: list[QuestionOptionOut]
    max_picks: int | None
    has_dont_know: bool
    has_other: bool


class MapFreeTextRequest(BaseModel):
    case_id: int
    question_id: str
    text: str


class MapFreeTextResponse(BaseModel):
    mapped_value: str | None
    """None if the LLM couldn't map it (or no LLM is configured) — the
    caller should store the raw text and mark the axis unmapped, per
    DESIGN.md, rather than force a guess."""
    used_llm: bool


class FollowUpPreviewOut(BaseModel):
    """What the ranking would lead with after this answer."""

    value: str
    label: str
    top_cause_id: str
    top_label: str
    top_likelihood: float


class NextFollowUpOut(BaseModel):
    question: QuestionOut
    reason: str
    """Why this question, in one sentence the operator reads."""
    previews: list[FollowUpPreviewOut]
