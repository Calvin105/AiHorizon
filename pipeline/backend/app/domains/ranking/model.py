from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RuleOverride(Base):
    """A rule whose weight an engineer changed from the rules page, and why.
    Deleting the row restores the manual's weight (ranking/weights.py)."""

    __tablename__ = "rule_overrides"

    rule_key: Mapped[str] = mapped_column(String(160), primary_key=True)
    weight: Mapped[float] = mapped_column(Float)
    note: Mapped[str] = mapped_column(Text)
    """Required: a weight that differs from the manual without a reason is
    exactly the untraceable number this system exists to avoid."""
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
