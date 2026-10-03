"""Every test gets an empty database and a real TestClient, offline.

The engine is built when app.core.database is first imported, from settings
read once — so the throwaway database path and a blank LLM key have to be in
the environment before any app module loads. Nothing here touches
pipeline.db or calls Groq.
"""

import json
import os
import tempfile
from pathlib import Path

_DB_DIR = Path(tempfile.mkdtemp(prefix="aihorizon-tests-"))
os.environ["SQLITE_PATH"] = str(_DB_DIR / "test.db")
os.environ["GROQ_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

import app.core.models  # registers every model on Base.metadata
from app.core.database import Base, engine
from app.domains.ranking import weights
from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[3]
SAMPLES = REPO_ROOT / "vision" / "samples"


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    weights.replace_all({})  # the manual's weights, whatever an earlier test edited
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def sample_geometry(name: str = "good") -> dict:
    sidecar = json.loads((SAMPLES / f"{name}.json").read_text())
    return {k: sidecar[k] for k in ("pattern", "width", "height", "profile")}


@pytest.fixture
def catalog(client):
    """One material, one station, and a profile laid out like vision/samples."""
    material = client.post("/api/materials", json={"name": "Epoxy A", "family": "epoxy"}).json()
    station = client.post(
        "/api/stations", json={"name": "Line 3", "line": "L3", "dispenser_class": "pressure_time"}
    ).json()
    profile = client.post(
        "/api/profiles",
        json={
            "name": "Demo grid", "material_id": material["material_id"],
            "spec_metric": "size_cv", "spec_limit": "< 0.15", "geometry": sample_geometry(),
        },
    ).json()
    return {"material": material, "station": station, "profile": profile}


def open_case(client, catalog, **extra) -> int:
    response = client.post(
        "/api/cases",
        json={
            "station_id": catalog["station"]["station_id"],
            "profile_id": catalog["profile"]["profile_id"],
            "complaint": "test", **extra,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["case_id"]


def photo_bytes(name: str) -> bytes:
    return (SAMPLES / f"{name}.png").read_bytes()


def post_photo(client, case_id: int, data: bytes, endpoint: str = "vision", **form) -> dict:
    response = client.post(
        f"/api/cases/{case_id}/{endpoint}",
        files={"photo": ("photo.png", data, "image/png")},
        data={k: str(v) for k, v in form.items()},
    )
    assert response.status_code == 200, response.text
    return response.json()
