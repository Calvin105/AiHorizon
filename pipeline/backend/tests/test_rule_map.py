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


# ---- the rules page: every rule listed, and editable --------------------------

AIR_PURGE = "air_in_fluid_path:response-purging-or-a-new-syringe-helps"
SIZE_SPREAD = "pressure_time_instability:size-varies-shot-to-shot-no-clear-pattern"
PURGED = {"axes": {"response": "purge_or_prime"}, "signals": {}, "followups": {}}


def _rule(body, key):
    return next(r for r in body["rules"] if r["key"] == key)


def _air(fingerprint):
    return next(c.likelihood for c in rank_causes(fingerprint) if c.cause_id == "air_in_fluid_path")


def test_every_rule_is_listed_once_with_what_fires_it():
    rules = rule_map().rules
    assert len(rules) == len({r.key for r in rules}) == sum(len(rs) for rs in CAUSE_RULES.values())
    assert all(r.triggers for r in rules)
    assert all(r.weight == r.manual_weight and r.note is None for r in rules)


def test_an_edit_changes_the_ranking_and_a_restore_undoes_it(client):
    prior = math.log(PRIOR / (1 - PRIOR))
    before = _air(PURGED)

    body = client.put(f"/api/rules/{AIR_PURGE}", json={"weight": 2.0, "note": "Seen on our line"}).json()
    rule = _rule(body, AIR_PURGE)
    assert (rule["manual_weight"], rule["weight"], rule["note"]) == (1.1, 2.0, "Seen on our line")
    assert math.isclose(_air(PURGED), 1 / (1 + math.exp(-(prior + 2.0))))
    hit = next(e for c in rank_causes(PURGED) if c.cause_id == "air_in_fluid_path" for e in c.evidence)
    assert hit.edited

    body = client.delete(f"/api/rules/{AIR_PURGE}").json()
    assert _rule(body, AIR_PURGE)["weight"] == 1.1
    assert _air(PURGED) == before


def test_zero_switches_a_rule_off_but_keeps_it_listed(client):
    body = client.put(f"/api/rules/{AIR_PURGE}", json={"weight": 0, "note": "Not on this line"}).json()
    assert not any(e.label.startswith("Response: purging") for c in rank_causes(PURGED) for e in c.evidence)
    rows = [r for g in body["groups"] for r in g["rows"]]
    cell = next(c for r in rows if r["id"] == "response:purge_or_prime" for c in r["cells"])
    assert cell["weight"] == 0


def test_an_edited_measurement_keeps_its_ramp(client):
    body = client.put(f"/api/rules/{SIZE_SPREAD}", json={"weight": 2.8, "note": "Doubled"}).json()
    rule = _rule(body, SIZE_SPREAD)
    assert rule["manual_weight"] == 1.4 and rule["full_strength"] == 4.2  # 2.8 at its 1.5 cap


def test_setting_the_manual_weight_back_is_a_restore(client):
    client.put(f"/api/rules/{AIR_PURGE}", json={"weight": 2.0, "note": "Trying it"})
    body = client.put(f"/api/rules/{AIR_PURGE}", json={"weight": 1.1, "note": "Back again"}).json()
    assert _rule(body, AIR_PURGE)["note"] is None


def test_edits_need_a_reason_and_a_real_rule(client):
    assert client.put(f"/api/rules/{AIR_PURGE}", json={"weight": 2.0, "note": ""}).status_code == 422
    assert client.put(f"/api/rules/{AIR_PURGE}", json={"weight": 9, "note": "Way up"}).status_code == 422
    assert client.put("/api/rules/no-such-rule", json={"weight": 1, "note": "Nope"}).status_code == 404


def test_saved_edits_come_back_after_a_restart(client):
    from app.core.database import SessionLocal
    from app.domains.ranking import overrides, weights

    client.put(f"/api/rules/{AIR_PURGE}", json={"weight": 2.0, "note": "Seen on our line"})
    weights.replace_all({})
    with SessionLocal() as db:
        overrides.load(db)
    assert weights.edited_weight(AIR_PURGE) == 2.0


def test_reload_follows_the_table_after_an_outside_reset(client):
    """The demo reset empties rule_overrides from another process; the
    running server only drops the edit it holds once it is told to reload."""
    from app.core.database import SessionLocal
    from app.domains.ranking import weights
    from app.domains.ranking.model import RuleOverride

    client.put(f"/api/rules/{AIR_PURGE}", json={"weight": 2.0, "note": "Seen on our line"})
    with SessionLocal() as db:
        db.query(RuleOverride).delete()
        db.commit()
    assert weights.edited_weight(AIR_PURGE) == 2.0  # still held in memory

    body = client.post("/api/rules/reload").json()
    assert weights.edited_weight(AIR_PURGE) is None
    assert _rule(body, AIR_PURGE)["weight"] == 1.1
