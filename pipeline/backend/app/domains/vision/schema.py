from pydantic import BaseModel


class VisionResultOut(BaseModel):
    quality_ok: bool
    quality_reason: str | None
    signals: dict[str, float | int]
    magnitude: str
    small_then_big_above_chance: bool
    cv_output: dict
