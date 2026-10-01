"""Rebuild the demo database from nothing, in one command, offline.

    uv run python -m app.reset_demo

What it leaves behind, and why each piece is there:

- The demo catalog (app/seed.py): profiles laid out like the sample photos,
  so a live photo measures instead of being refused.
- Four showcase cases, driven through the real API in-process — nothing is
  written to the tables directly, so each one is what the pipeline itself
  produced:
    1  CONFIRMED   size varies → air in the syringe; one purge, re-measured
                   back in spec, held 30 shots
    2  PLAUSIBLE   missing dots → carryover; dispense time raised, but the
                   re-measurement still shows a missing deposit
    3  UNVERIFIED  closed without anything proved — the gap list says so
    4  waiting     a wrong-shape case the operator escalated to an engineer
- 24 closed history cases (app/seed_history.py), so the learning-database
  read has a past to count. The showcase cases are re-ranked once it
  exists, so their Gate B notes read against it.

The old database is moved to backups/ first, never deleted. The LLM is off
for the rebuild, so it needs no network and comes out the same every time;
a case opened live afterwards can still use it.
"""

import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

os.environ["LLM_ENABLED"] = "false"

from alembic.config import Config
from fastapi.testclient import TestClient

from alembic import command
from app.core.config import BACKEND_ROOT, get_settings

SAMPLES = Path(__file__).resolve().parents[3] / "vision" / "samples"


def _backup_and_clear(db_path: Path) -> Path | None:
    if not db_path.exists():
        return None
    backups = BACKEND_ROOT / "backups"
    backups.mkdir(exist_ok=True)
    target = backups / f"{db_path.stem}-{datetime.now(UTC):%Y%m%d-%H%M%S}Z.db"
    shutil.move(db_path, target)
    return target


def _photo(client: TestClient, case_id: int, name: str, endpoint: str = "vision", **form) -> dict:
    with (SAMPLES / f"{name}.png").open("rb") as fh:
        response = client.post(
            f"/cases/{case_id}/{endpoint}", files={"photo": (f"{name}.png", fh, "image/png")},
            data={k: str(v) for k, v in form.items()},
        )
    response.raise_for_status()
    return response.json()


def _open(client: TestClient, profile_id: int, station_id: int, complaint: str, text: str) -> int:
    response = client.post(
        "/cases",
        json={"station_id": station_id, "profile_id": profile_id, "complaint": complaint, "complaint_text": text},
    )
    response.raise_for_status()
    return response.json()["case_id"]


def _answer(client: TestClient, case_id: int, axes: dict, followups: dict | None = None) -> None:
    fingerprint: dict = {"axes": axes}
    if followups:
        fingerprint["followups"] = followups
    client.patch(f"/cases/{case_id}", json={"fingerprint": fingerprint}).raise_for_status()


def _check(client: TestClient, case_id: int, name: str, cause_id: str, *, change: bool, outcome: str, detail: str):
    client.post(
        f"/cases/{case_id}/check-results",
        json={"check_name": name, "cause_id": cause_id, "is_change": change, "outcome": outcome,
              "result_detail": detail},
    ).raise_for_status()


def _plausible_case(client: TestClient, profile_id: int, station_id: int) -> int:
    case_id = _open(
        client, profile_id, station_id, "Missing or starved deposit",
        "Some dots don't come out at all, and the one after a gap looks fat.",
    )
    _photo(client, case_id, "missing_carryover")
    _answer(
        client, case_id,
        {"signature": ["missing"], "trajectory": "always_been_like_this", "footprint": "recipe",
         "inputs": ["nothing_unusual"], "response": "raise_pressure_or_time"},
    )
    client.post(f"/cases/{case_id}/rank").raise_for_status()
    _check(client, case_id, "Check the next dot after each small one", "volume_too_small_carryover",
           change=False, outcome="confirms", detail="Every gap is followed by an oversized dot.")
    _check(client, case_id, "Increase dispense time in small steps within your process spec",
           "volume_too_small_carryover", change=True, outcome="confirms",
           detail="Dispense time raised one step, engineer approved.")
    # ghost.png still has a deposit missing: the fix is not proved.
    _photo(client, case_id, "ghost", "verify", shots_measured=40)
    client.post(f"/cases/{case_id}/close").raise_for_status()
    return case_id


def _unverified_case(client: TestClient, profile_id: int, station_id: int) -> int:
    case_id = _open(
        client, profile_id, station_id, "Inconsistent size shot to shot",
        "Night shift says the dots looked uneven. Closed at shift end before anyone checked.",
    )
    _answer(
        client, case_id,
        {"signature": ["size_varies"], "trajectory": "random", "footprint": "not_tested",
         "inputs": ["dont_know"], "response": "not_tried"},
    )
    client.post(f"/cases/{case_id}/rank").raise_for_status()
    client.post(f"/cases/{case_id}/close").raise_for_status()
    return case_id


def _escalated_case(client: TestClient, profile_id: int, station_id: int) -> int:
    case_id = _open(
        client, profile_id, station_id, "Air bubbles or abnormal shapes",
        "A few dots have a tail on them, not every board.",
    )
    _photo(client, case_id, "abnormal_shape")
    _answer(
        client, case_id,
        {"signature": ["wrong_shape"], "trajectory": "random", "footprint": "not_tested",
         "inputs": ["nothing_unusual"], "response": "not_tried"},
    )
    client.post(f"/cases/{case_id}/rank").raise_for_status()
    client.patch(
        f"/cases/{case_id}",
        json={"escalate": True, "escalation_note": "The checks don't match what I'm seeing"},
    ).raise_for_status()
    return case_id


def main() -> None:
    from app.main import app
    from app.seed import seed
    from app.seed_demo_case import main as confirmed_case
    from app.seed_history import seed_history

    settings = get_settings()
    db_path = Path(settings.database_url.removeprefix("sqlite:///"))
    moved = _backup_and_clear(db_path)
    if moved:
        print(f"Moved the old database to {moved}")

    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    command.upgrade(config, "head")
    seed()

    with TestClient(app, base_url="http://testserver/api") as client:
        profile = next(p for p in client.get("/profiles").json()["items"] if p["material"]["family"] == "epoxy")
        station_id = client.get("/stations").json()["items"][0]["station_id"]

        showcase = {"CONFIRMED": confirmed_case(client)}
        showcase["PLAUSIBLE"] = _plausible_case(client, profile["profile_id"], station_id)
        showcase["UNVERIFIED"] = _unverified_case(client, profile["profile_id"], station_id)
        showcase["waiting for an engineer"] = _escalated_case(client, profile["profile_id"], station_id)

        seed_history()
        for case_id in showcase.values():
            client.post(f"/cases/{case_id}/rank").raise_for_status()

    print("\nDemo database rebuilt. Showcase cases:")
    for label, case_id in showcase.items():
        print(f"  #{case_id:<3} {label:<24} http://localhost:3001/cases/{case_id}")
    print("Open a fresh case for the live run at http://localhost:3001/troubleshoot")


if __name__ == "__main__":
    main()
