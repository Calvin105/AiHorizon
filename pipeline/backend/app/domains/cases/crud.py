from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.domains.cases.model import Case
from app.domains.cases.schema import CaseOpen, CaseUpdate
from app.domains.profiles.model import DispenseProfile


def _loaded(query):
    return query.options(
        selectinload(Case.station),
        selectinload(Case.profile).selectinload(DispenseProfile.material),
        selectinload(Case.check_results),
    )


def list_cases(db: Session, *, limit: int, offset: int) -> tuple[list[Case], int]:
    total = db.scalar(select(func.count()).select_from(Case)) or 0
    items = list(
        db.scalars(_loaded(select(Case)).order_by(Case.opened_at.desc()).limit(limit).offset(offset))
    )
    return items, total


def get_case(db: Session, case_id: int) -> Case | None:
    return db.scalar(_loaded(select(Case)).where(Case.case_id == case_id))


def open_case(db: Session, data: CaseOpen) -> Case:
    case = Case(opened_at=datetime.now(UTC), **data.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def update_case(db: Session, case: Case, data: CaseUpdate) -> Case:
    patch = data.model_dump(mode="json", exclude_unset=True)

    # The fingerprint has two halves with two different owners: the
    # interview writes `axes`, step 3 writes `signals`. A client saving
    # answers has no measurements to send and posts `signals: {}`, so a
    # wholesale assignment let every answer erase what the photo measured.
    #
    # That was silent and expensive: Gate A then reported "no measured
    # signal behind it — only answers" on every photographed case, Gate B
    # could never match (it scores signals), and verification had no
    # `before` to diff against. The image pipeline was running and being
    # thrown away.
    #
    # Merged per key, incoming winning, so a caller that does send a real
    # measurement still overwrites the old one.
    incoming = patch.get("fingerprint")
    if isinstance(incoming, dict):
        existing_signals = (case.fingerprint or {}).get("signals") or {}
        if existing_signals:
            merged = {**existing_signals, **(incoming.get("signals") or {})}
            patch["fingerprint"] = {**incoming, "signals": merged}

    for field, value in patch.items():
        setattr(case, field, value)
    db.commit()
    db.refresh(case)
    return case
