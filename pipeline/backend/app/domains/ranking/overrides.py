"""Saving and loading engineer edits to rule weights. ranking/weights.py
holds the ones in force; this keeps it in step with the rule_overrides
table, at startup and after every edit."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.domains.ranking import weights
from app.domains.ranking.model import RuleOverride
from app.domains.ranking.rules import CAUSE_RULES, CauseRule


def find_rule(key: str) -> CauseRule | None:
    for cause_id, rules in CAUSE_RULES.items():
        for rule in rules:
            if weights.rule_key(cause_id, rule) == key:
                return rule
    return None


def saved(db: Session) -> dict[str, RuleOverride]:
    """Every saved edit, by rule key. A database from before rule editing
    has no table yet, which reads as no edits rather than as an error."""
    try:
        return {row.rule_key: row for row in db.scalars(select(RuleOverride))}
    except OperationalError:
        db.rollback()
        return {}


def load(db: Session) -> None:
    weights.replace_all({key: row.weight for key, row in saved(db).items()})


def save(db: Session, rule: CauseRule, key: str, weight: float, note: str) -> None:
    """Setting a rule back to the manual's weight is a restore, not an edit."""
    if weight == rule.evaluate.weight:
        restore(db, key)
        return
    row = db.get(RuleOverride, key)
    if row is None:
        db.add(RuleOverride(rule_key=key, weight=weight, note=note, updated_at=datetime.now(UTC)))
    else:
        row.weight, row.note, row.updated_at = weight, note, datetime.now(UTC)
    db.commit()
    load(db)


def restore(db: Session, key: str) -> None:
    row = db.get(RuleOverride, key)
    if row is not None:
        db.delete(row)
        db.commit()
    load(db)
