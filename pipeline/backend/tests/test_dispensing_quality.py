"""Bonus 2's quality score: stars per aspect and an overall out of 100,
each one a count of deposits that can be checked on the annotated photo."""

from tests.conftest import open_case, photo_bytes, post_photo
from tests.test_vision_router import _unalignable


def _aspects(quality: dict) -> dict:
    return {a["key"]: (a["stars"], a["passed"], a["total"]) for a in quality["aspects"]}


def test_a_good_photo_scores_full_marks(client, catalog):
    quality = post_photo(client, open_case(client, catalog), photo_bytes("good"))["dispensing_quality"]
    assert quality["overall"] == 100
    assert all(stars == 5 for stars, _, _ in _aspects(quality).values())


def test_scatter_costs_size_and_nothing_else(client, catalog):
    quality = post_photo(client, open_case(client, catalog), photo_bytes("inconsistent"))["dispensing_quality"]
    aspects = _aspects(quality)
    assert aspects["size"] == (1, 3, 15)  # three deposits landed within 15% of nominal
    assert aspects["completeness"] == aspects["shape"] == aspects["position"] == (5, 15, 15)
    assert quality["overall"] == 20


def test_a_single_failure_always_costs_a_star(client, catalog):
    quality = post_photo(client, open_case(client, catalog), photo_bytes("ghost"))["dispensing_quality"]
    assert _aspects(quality)["completeness"] == (4, 14, 15)


def test_the_report_carries_it(client, catalog):
    case_id = open_case(client, catalog)
    post_photo(client, case_id, photo_bytes("inconsistent"))
    client.post(f"/api/cases/{case_id}/rank")
    report = client.get(f"/api/cases/{case_id}/report", params={"use_llm_explanation": False}).json()
    assert report["defect"]["dispensing_quality"]["overall"] == 20


def test_a_photo_that_could_not_be_measured_is_not_rated(client, catalog):
    result = post_photo(client, open_case(client, catalog), _unalignable("inconsistent"))
    assert result["quality_ok"] is False
    assert result["dispensing_quality"] is None
