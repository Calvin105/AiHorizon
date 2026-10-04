"""Step 5's tier: a check that confirms the top cause settles it, and every
tier says what it rests on."""

from app.domains.ranking.gates import GateAResult, GateBResult
from app.domains.ranking.tier import compute_tier, tier_reason
from tests.conftest import open_case, photo_bytes, post_photo

AT_CHANCE = GateAResult(above_chance=False, deciding_signal="Size varies", p_value=None, note="")
NO_PRECEDENT = GateBResult(applied=False, matched_count=0, contradicting_count=0, note="")

AIR_CASE = {
    "axes": {
        "signature": ["size_varies"], "trajectory": "random", "footprint": "material",
        "inputs": ["new_lot_or_syringe"], "response": "purge_or_prime",
    },
}


def _ranked_case(client, catalog) -> int:
    case_id = open_case(client, catalog)
    post_photo(client, case_id, photo_bytes("inconsistent"))
    client.patch(f"/api/cases/{case_id}", json={"fingerprint": AIR_CASE})
    client.post(f"/api/cases/{case_id}/rank")
    return case_id


def _check(client, case_id, cause_id, outcome) -> dict:
    response = client.post(
        f"/api/cases/{case_id}/check-results",
        json={"check_name": "Hold the syringe up to the light", "cause_id": cause_id,
              "is_change": False, "outcome": outcome},
    )
    assert response.status_code == 201, response.text
    return client.post(f"/api/cases/{case_id}/rank").json()


def test_a_lead_from_answers_alone_stays_provisional_and_says_why(client, catalog):
    # The photo's size spread backs pressure/time, not air, which leads on
    # the answers alone.
    ranking = client.post(f"/api/cases/{_ranked_case(client, catalog)}/rank").json()
    assert ranking["tier"] == "T2"
    assert ranking["tier_reason"] == (
        "Provisional: nothing measured in a photo backs it and fewer than 3 matching confirmed cases "
        "back it. A check that confirms it would settle it."
    )


def test_a_check_that_confirms_the_top_cause_reaches_t1(client, catalog):
    case_id = _ranked_case(client, catalog)
    ranking = _check(client, case_id, "air_in_fluid_path", "confirms")
    assert ranking["top_cause_id"] == "air_in_fluid_path"
    assert ranking["tier"] == "T1"
    assert ranking["tier_reason"] == "A check on this case confirmed air trapped in the syringe or material supply."


def test_checks_confirming_two_causes_settle_nothing(client, catalog):
    case_id = _ranked_case(client, catalog)
    _check(client, case_id, "air_in_fluid_path", "confirms")
    ranking = _check(client, case_id, "pressure_time_instability", "confirms")
    assert ranking["tier"] == "T2"


def test_a_check_outweighs_a_critic_that_read_the_complaint_differently():
    # Pass 2 needs an LLM, so this is the tier table on its own: the critic
    # disagreed and nothing measured beats chance, which alone is T4.
    assert compute_tier(False, AT_CHANCE, NO_PRECEDENT) == "T4"
    assert compute_tier(False, AT_CHANCE, NO_PRECEDENT, check_confirmed=True) == "T1"
    reason = tier_reason(
        "T1", top_label="Air in the line", critic_label="Nozzle blockage",
        gate_a=AT_CHANCE, gate_b=NO_PRECEDENT, check_confirmed=True,
    )
    assert reason.startswith("A check on this case confirmed air in the line.")
    assert "nozzle blockage" in reason


def test_t4_names_the_split():
    reason = tier_reason(
        "T4", top_label="Air in the line", critic_label="Nozzle blockage",
        gate_a=AT_CHANCE, gate_b=NO_PRECEDENT, check_confirmed=False,
    )
    assert reason.startswith("The second read picked nozzle blockage, and nothing measured separates the two.")


def test_the_ranking_and_the_report_count_what_backs_the_top_cause(client, catalog):
    case_id = _ranked_case(client, catalog)
    ranking = _check(client, case_id, "air_in_fluid_path", "confirms")
    backing = ranking["backing"]
    top = ranking["pass1"][0]["evidence"]
    assert backing["reasons"] == sum(e["weight"] > 0 for e in top)
    assert backing["checks"] == 1
    assert backing["measured"] + backing["answers"] + backing["checks"] == backing["reasons"]

    report = client.get(f"/api/cases/{case_id}/report", params={"use_llm_explanation": False}).json()
    assert report["backing"] == backing
    assert report["tier_reason"] == ranking["tier_reason"]
    assert "stars" not in report["defect"]
