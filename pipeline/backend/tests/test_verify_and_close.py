"""Step 7's re-measure and step 8's close: CONFIRMED has to mean proved."""

from tests.conftest import open_case, photo_bytes, post_photo

FINGERPRINT = {
    "axes": {
        "signature": ["size_varies"], "trajectory": "random", "footprint": "material",
        "inputs": ["new_lot_or_syringe"], "response": "purge_or_prime",
    },
}


def _check(client, case_id, name, cause_id, *, change, outcome="confirms"):
    response = client.post(
        f"/api/cases/{case_id}/check-results",
        json={"check_name": name, "cause_id": cause_id, "is_change": change, "outcome": outcome},
    )
    assert response.status_code == 201, response.text


def _proved_case(
    client, catalog, *, before="inconsistent", change_cause="air_in_fluid_path", change_outcome="confirms",
):
    case_id = open_case(client, catalog)
    if before:
        post_photo(client, case_id, photo_bytes(before))
    client.patch(f"/api/cases/{case_id}", json={"fingerprint": FINGERPRINT})
    client.post(f"/api/cases/{case_id}/rank")
    _check(client, case_id, "Hold the syringe up to the light", "air_in_fluid_path", change=False)
    _check(client, case_id, "Purge the line", change_cause, change=True, outcome=change_outcome)
    return case_id


def test_the_happy_path_closes_confirmed(client, catalog):
    case_id = _proved_case(client, catalog)
    verification = post_photo(client, case_id, photo_bytes("good"), "verify", shots_measured=30)
    assert verification["in_spec"] is True
    assert verification["signal"] == "size_cv"
    close = client.post(f"/api/cases/{case_id}/close").json()
    assert close["tier"] == "CONFIRMED", close["gaps"]


def test_verify_fails_when_a_deposit_is_still_missing(client, catalog):
    case_id = _proved_case(client, catalog)
    # ghost.png measures a size spread well inside spec, with one deposit
    # missing. Re-measuring size_cv alone called that "back in spec".
    verification = post_photo(client, case_id, photo_bytes("ghost"), "verify", shots_measured=30)
    assert verification["in_spec"] is False
    failed = [c["signal"] for c in verification["checks"] if not c["ok"]]
    assert failed == ["missing_count"]


def test_verify_reports_the_signal_that_was_out_of_spec_before(client, catalog):
    case_id = _proved_case(client, catalog, before="ghost")
    verification = post_photo(client, case_id, photo_bytes("good"), "verify", shots_measured=30)
    assert verification["signal"] == "missing_count"
    assert verification["before"] == 1
    assert verification["after"] == 0


def test_verify_counts_the_deposits_it_measured(client, catalog):
    case_id = _proved_case(client, catalog)
    verification = post_photo(client, case_id, photo_bytes("good"), "verify", shots_measured=30)
    assert verification["deposits_measured"] == 15
    assert verification["shots_source"] == "operator"


def test_a_change_aimed_at_another_cause_cannot_confirm(client, catalog):
    # Air confirmed by a look, then the needle changed: the symptom going
    # away cannot be credited to air.
    case_id = _proved_case(client, catalog, change_cause="nozzle_blockage", change_outcome="inconclusive")
    post_photo(client, case_id, photo_bytes("good"), "verify", shots_measured=30)
    close = client.post(f"/api/cases/{case_id}/close").json()
    assert close["tier"] == "PLAUSIBLE"
    assert any("not the confirmed cause" in gap for gap in close["gaps"])


def test_checks_confirming_two_causes_cannot_confirm(client, catalog):
    # A look confirmed air, then the needle change "confirmed" a blockage:
    # the record cannot say which it was, so it may not claim either.
    case_id = _proved_case(client, catalog, change_cause="nozzle_blockage")
    post_photo(client, case_id, photo_bytes("good"), "verify", shots_measured=30)
    close = client.post(f"/api/cases/{case_id}/close").json()
    assert close["tier"] == "PLAUSIBLE"
    assert any("different causes" in gap for gap in close["gaps"])


def test_no_before_photo_cannot_confirm(client, catalog):
    case_id = _proved_case(client, catalog, before=None)
    post_photo(client, case_id, photo_bytes("good"), "verify", shots_measured=30)
    close = client.post(f"/api/cases/{case_id}/close").json()
    assert close["tier"] == "PLAUSIBLE"
    assert any("before" in gap for gap in close["gaps"])


def test_short_hold_cannot_confirm(client, catalog):
    case_id = _proved_case(client, catalog)
    post_photo(client, case_id, photo_bytes("good"), "verify", shots_measured=10)
    close = client.post(f"/api/cases/{case_id}/close").json()
    assert close["tier"] == "PLAUSIBLE"


def test_nothing_proved_is_unverified(client, catalog):
    case_id = open_case(client, catalog)
    close = client.post(f"/api/cases/{case_id}/close").json()
    assert close["tier"] == "UNVERIFIED"
    assert len(close["gaps"]) == 5
