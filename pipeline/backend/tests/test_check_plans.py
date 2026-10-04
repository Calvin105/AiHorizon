"""Each cause's troubleshooting plan: the steps the wizard shows once a
cause is picked, and the report recommends from."""

from app.domains.causes.vocabulary import load_causes


def test_every_cause_has_a_look_then_a_change_and_says_what_each_result_means(client):
    plans = client.get("/api/causes/checks").json()
    assert set(plans) == {c["id"] for c in load_causes()}
    for cause_id, steps in plans.items():
        # Looking first: the loop can afford any number of looks, but only
        # one change before CONFIRMED is out of reach.
        assert [s["is_change"] for s in steps] == [False, True], cause_id
        for step in steps:
            assert step["confirms_if"] and step["rules_out_if"], step["name"]
            assert step["confirms_if"] != step["rules_out_if"]
