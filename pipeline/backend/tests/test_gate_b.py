"""Gate B's precedent has to be a similar problem, not just a confirmed one."""

from datetime import UTC, datetime

from app.core.database import SessionLocal
from app.domains.cases.model import Case
from app.domains.enums import CaseTier
from app.domains.retrieval.fine import fine_match
from tests.conftest import open_case, photo_bytes, post_photo


def _confirmed(db, catalog, size_cv: float, cause_id: str, *, profile_id=None) -> int:
    case = Case(
        station_id=catalog["station"]["station_id"],
        profile_id=profile_id or catalog["profile"]["profile_id"],
        opened_at=datetime.now(UTC),
        fingerprint={"axes": {}, "signals": {"size_cv": size_cv, "missing_count": 0}},
        diagnosis={"cause_id": cause_id},
        tier=CaseTier.CONFIRMED,
    )
    db.add(case)
    db.commit()
    return case.case_id


def test_only_confirmed_cases_with_similar_signals_match(client, catalog):
    case_id = open_case(client, catalog)
    post_photo(client, case_id, photo_bytes("inconsistent"))  # size_cv ~0.49
    with SessionLocal() as db:
        near = [_confirmed(db, catalog, cv, "air_in_fluid_path") for cv in (0.45, 0.5, 0.53)]
        far = _confirmed(db, catalog, 0.06, "nozzle_blockage")
        case = db.get(Case, case_id)
        matched = {m.case_id for m in fine_match(db, case)}
    assert set(near) <= matched
    assert far not in matched


def test_other_materials_are_not_precedent(client, catalog):
    silicone = client.post("/api/materials", json={"name": "Sil", "family": "silicone"}).json()
    other_profile = client.post(
        "/api/profiles", json={"name": "Silicone job", "material_id": silicone["material_id"]},
    ).json()
    case_id = open_case(client, catalog)
    post_photo(client, case_id, photo_bytes("inconsistent"))
    with SessionLocal() as db:
        other = _confirmed(db, catalog, 0.49, "air_in_fluid_path", profile_id=other_profile["profile_id"])
        case = db.get(Case, case_id)
        matched = {m.case_id for m in fine_match(db, case)}
    assert other not in matched
