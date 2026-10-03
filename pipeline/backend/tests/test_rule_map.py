"""The home page's rule table is the rule engine read out, never a copy."""

import math

from app.domains.ranking.pass1 import PRIOR, rank_causes
from app.domains.ranking.rule_map import EMPTY_FINGERPRINT, fires, rule_map
from app.domains.ranking.rules import CAUSE_RULES


def _rows():
    return {row.id: row for group in rule_map().groups for row in group.rows}


def test_every_rule_is_in_the_table():
    shown = {(cell.cause_id, cell.label) for row in _rows().values() for cell in row.cells}
    defined = {(cause_id, rule.label) for cause_id, rules in CAUSE_RULES.items() for rule in rules}
    assert shown == defined


def test_nothing_fires_on_an_empty_case():
    # A rule that fired with nothing known would count in every row at once.
    assert fires(EMPTY_FINGERPRINT) == {}


def test_adding_up_ticked_rows_reproduces_the_ranking():
    """What the home page does when rows are ticked: start every cause at the
    prior and add the ticked rows' weights. The demo case, with its follow-up."""
    ticked = [
        "photo:size_cv", "trajectory:random", "footprint:material",
        "response:purge_or_prime", "followup:pressure_gauge:steady",
    ]
    totals: dict[str, float] = {}
    for row_id in ticked:
        for cell in _rows()[row_id].cells:
            totals[cell.cause_id] = totals.get(cell.cause_id, 0.0) + cell.weight

    fingerprint = {
        "axes": {"trajectory": "random", "footprint": "material", "response": "purge_or_prime"},
        "signals": {"size_cv": 0.45},
        "followups": {"pressure_gauge": "steady"},
    }
    prior = math.log(PRIOR / (1 - PRIOR))
    ranked = {c.cause_id: c.likelihood for c in rank_causes(fingerprint)}
    for cause_id, likelihood in ranked.items():
        assert math.isclose(likelihood, 1 / (1 + math.exp(-(prior + totals.get(cause_id, 0.0)))), abs_tol=1e-3)
    assert round(ranked["air_in_fluid_path"] * 100) == 59
    assert round(ranked["pressure_time_instability"] * 100) == 44


def test_measurements_show_their_ramp():
    size = _rows()["photo:size_cv"].cells
    assert [c.cause_id for c in size] == ["pressure_time_instability"]
    assert size[0].weight_mild is not None and size[0].weight_mild < size[0].weight


def test_rules_endpoint(client):
    response = client.get("/api/rules")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["rule_count"] == sum(len(rules) for rules in CAUSE_RULES.values())
    assert [c["cause_id"] for c in body["causes"]] == list(CAUSE_RULES)
    assert body["groups"][0]["kind"] == "measured"
