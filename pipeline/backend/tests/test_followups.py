"""Adaptive follow-ups: asked only when an answer can move the ranking."""

from tests.conftest import open_case

SPINE = {
    "signature": ["size_varies"], "trajectory": "sudden_step", "footprint": "not_tested",
    "inputs": ["nothing_unusual"], "response": "not_tried",
}


def _answer(client, case_id, axes, followups=None):
    fingerprint = {"axes": axes}
    if followups is not None:
        fingerprint["followups"] = followups
    response = client.patch(f"/api/cases/{case_id}", json={"fingerprint": fingerprint})
    assert response.status_code == 200, response.text


def _next(client, case_id):
    response = client.get("/api/intake/followups/next", params={"case_id": case_id})
    assert response.status_code == 200, response.text
    return response.json()


def test_a_sudden_start_gets_a_follow_up_with_its_reason(client, catalog):
    case_id = open_case(client, catalog)
    _answer(client, case_id, SPINE)
    followup = _next(client, case_id)
    assert followup is not None
    assert followup["question"]["id"] in {"recent_change", "location", "pressure_gauge", "next_dot"}
    assert followup["reason"].startswith("Asked because")
    assert {p["value"] for p in followup["previews"]} == {o["value"] for o in followup["question"]["options"]}


def test_the_answer_moves_the_ranking(client, catalog):
    case_id = open_case(client, catalog)
    _answer(client, case_id, SPINE)
    before = client.post(f"/api/cases/{case_id}/rank").json()["pass1"]
    _answer(client, case_id, SPINE, {"recent_change": "fixture_changed"})
    after = client.post(f"/api/cases/{case_id}/rank").json()["pass1"]
    p_before = {c["cause_id"]: c["likelihood"] for c in before}
    p_after = {c["cause_id"]: c["likelihood"] for c in after}
    assert p_after["dispense_height_or_board_bending"] > p_before["dispense_height_or_board_bending"] + 0.1


def test_at_most_two_are_asked(client, catalog):
    case_id = open_case(client, catalog)
    _answer(client, case_id, SPINE, {"recent_change": "nothing_known", "location": "random_spots"})
    assert _next(client, case_id) is None


def test_an_answered_follow_up_is_not_asked_again(client, catalog):
    case_id = open_case(client, catalog)
    _answer(client, case_id, SPINE)
    first = _next(client, case_id)["question"]
    _answer(client, case_id, SPINE, {first["id"]: first["options"][0]["value"]})
    second = _next(client, case_id)
    assert second is None or second["question"]["id"] != first["id"]


def test_a_save_without_follow_ups_keeps_them(client, catalog):
    case_id = open_case(client, catalog)
    _answer(client, case_id, SPINE, {"location": "one_area"})
    _answer(client, case_id, SPINE)  # e.g. a later answer save that only sends axes
    stored = client.get(f"/api/cases/{case_id}").json()["fingerprint"]["followups"]
    assert stored == {"location": "one_area"}


def test_follow_ups_never_enter_case_matching(client, catalog):
    case_id = open_case(client, catalog)
    _answer(client, case_id, SPINE, {"location": "one_area"})
    axes = client.get(f"/api/cases/{case_id}").json()["fingerprint"]["axes"]
    assert "location" not in axes


def test_nothing_is_asked_when_nothing_applies(client, catalog):
    case_id = open_case(client, catalog)
    _answer(client, case_id, {"signature": [], "trajectory": "gradual"})
    assert _next(client, case_id) is None
