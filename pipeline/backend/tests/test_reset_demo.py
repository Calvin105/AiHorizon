"""The demo reset: one command, safe with the demo running."""

import sqlite3
from contextlib import closing
from pathlib import Path

from app import reset_demo
from app.core.config import get_settings
from app.core.database import Base, engine


def test_reset_rebuilds_in_place_for_a_server_already_connected(tmp_path, monkeypatch):
    monkeypatch.setattr(reset_demo, "BACKUPS", tmp_path)
    told = []
    monkeypatch.setattr(reset_demo, "_tell_running_backend", lambda: told.append(True))
    # Alembic builds the schema itself, so start from no tables at all.
    Base.metadata.drop_all(engine)

    reset_demo.main()
    db_path = Path(get_settings().database_url.removeprefix("sqlite:///"))

    # A connection opened before the second reset stands in for the running
    # backend. Moving the file away used to leave it on the old copy.
    with closing(sqlite3.connect(db_path)) as server:
        server.execute("UPDATE cases SET complaint = 'edited during the demo' WHERE case_id = 1")
        server.commit()

        reset_demo.main()

        ids = [row[0] for row in server.execute("SELECT case_id FROM cases ORDER BY case_id")]
        complaint = server.execute("SELECT complaint FROM cases WHERE case_id = 1").fetchone()[0]

    assert ids == list(range(1, len(ids) + 1)), "case numbers restart at 1, so the showcase is #1-#4"
    assert len(ids) == 33  # four showcase cases and 29 history cases, not twice that
    assert complaint != "edited during the demo"
    assert len(list(tmp_path.glob("*.db"))) == 2  # each run kept a copy of what it replaced
    assert told == [True, True]
