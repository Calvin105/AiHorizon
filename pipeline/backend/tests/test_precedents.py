"""The learning-database sentence must not invent a leader out of a tie."""

from datetime import UTC, datetime

from app.core.database import SessionLocal
from app.domains.cases.model import Case
from app.domains.enums import CaseTier
from app.domains.retrieval.precedents import precedent_stats
from tests.conftest import open_case

AXES = {
    "signature": ["missing"], "trajectory": "always_been_like_this", "footprint": "recipe",
    "inputs": ["nothing_unusual"], "response": "raise_pressure_or_time",
}


def test_a_tie_is_reported_as_a_tie(client, catalog):
    case_id = open_case(client, catalog)
    client.patch(f"/api/cases/{case_id}", json={"fingerprint": {"axes": AXES}})
    with SessionLocal() as db:
        for cause in ["nozzle_blockage", "nozzle_blockage", "volume_too_small_carryover", "volume_too_small_carryover"]:
            db.add(Case(
                station_id=catalog["station"]["station_id"], profile_id=catalog["profile"]["profile_id"],
                opened_at=datetime.now(UTC), fingerprint={"axes": AXES, "signals": {}},
                diagnosis={"cause_id": cause}, tier=CaseTier.CONFIRMED,
            ))
        db.commit()
        stats = precedent_stats(db, db.get(Case, case_id))
    assert stats.sentence is not None
    assert "2 cases each" in stats.sentence
    assert " or " in stats.sentence
