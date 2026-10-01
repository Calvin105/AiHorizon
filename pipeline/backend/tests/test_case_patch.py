"""The generic PATCH is for what an operator or engineer actually types.
Everything step 8 rests on is written only by the step endpoints."""

import pytest

from tests.conftest import open_case, photo_bytes, post_photo


@pytest.mark.parametrize(
    "field, value",
    [
        ("tier", "CONFIRMED"),
        ("resolved", True),
        ("diagnosis", {"cause_id": "nozzle_blockage", "confirmed_by": {"check": "x", "result": "y"}}),
        ("verification", {"signal": "size_cv", "before": 0.4, "after": 0.05, "in_spec": True, "shots_measured": 50}),
        ("ranking", {"tier": "T1"}),
        ("rank_tier", "T1"),
        ("closed_at", "2026-10-01T00:00:00Z"),
        ("vision_result", {"quality_ok": True}),
        ("diagnosed", "check_confirmed"),
    ],
)
def test_close_record_fields_cannot_be_patched(client, catalog, field, value):
    case_id = open_case(client, catalog)
    response = client.patch(f"/api/cases/{case_id}", json={field: value})
    assert response.status_code == 422
    case = client.get(f"/api/cases/{case_id}").json()
    assert case["tier"] is None
    assert case["resolved"] is False


def test_operator_and_engineer_fields_still_patch(client, catalog):
    case_id = open_case(client, catalog)
    response = client.patch(
        f"/api/cases/{case_id}",
        json={"engineer_notes": "re-seat the needle", "escalate": True, "escalation_note": "stuck"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["engineer_notes"] == "re-seat the needle"
    assert body["escalate"] is True


def test_client_cannot_write_measured_signals(client, catalog):
    case_id = open_case(client, catalog)
    measured = post_photo(client, case_id, photo_bytes("inconsistent"))["signals"]["size_cv"]
    client.patch(
        f"/api/cases/{case_id}",
        json={"fingerprint": {"axes": {"signature": ["size_varies"]}, "signals": {"size_cv": 0.01}}},
    )
    stored = client.get(f"/api/cases/{case_id}").json()["fingerprint"]["signals"]
    assert stored["size_cv"] == measured


def test_client_cannot_add_or_drop_the_image_only_signature(client, catalog):
    case_id = open_case(client, catalog)
    post_photo(client, case_id, photo_bytes("missing_carryover"))
    # The picker never offers small_then_big, so a save of the operator's own
    # picks arrives without it — it must survive that save.
    client.patch(f"/api/cases/{case_id}", json={"fingerprint": {"axes": {"signature": ["missing"]}}})
    axes = client.get(f"/api/cases/{case_id}").json()["fingerprint"]["axes"]
    assert set(axes["signature"]) == {"missing", "small_then_big"}

    other = open_case(client, catalog)
    client.patch(f"/api/cases/{other}", json={"fingerprint": {"axes": {"signature": ["small_then_big"]}}})
    axes = client.get(f"/api/cases/{other}").json()["fingerprint"]["axes"]
    assert "small_then_big" not in axes["signature"]
