"""A profile's spec only counts as a size-spread limit when it is one."""

import pytest

from app.domains.vision.magnitude import (
    DEFAULT_SPEC_LIMIT,
    bucket_magnitude,
    parse_spec_limit,
)
from tests.conftest import open_case, photo_bytes, post_photo, sample_geometry


@pytest.mark.parametrize(
    "spec_limit, spec_metric, expected",
    [
        ("< 0.15", "size_cv", 0.15),
        ("<= 0.2", "size_cv", 0.2),
        ("0.1", "size_cv", 0.1),
        ("≤ 0.12", None, 0.12),
        (None, "size_cv", DEFAULT_SPEC_LIMIT),
        # A diameter tolerance is not a size_cv limit. It used to parse as 500.
        ("500±50", "dot_diameter_um", DEFAULT_SPEC_LIMIT),
        ("500±50", "size_cv", DEFAULT_SPEC_LIMIT),
        ("< 1.5", "size_cv", DEFAULT_SPEC_LIMIT),
    ],
)
def test_parse_spec_limit(spec_limit, spec_metric, expected):
    assert parse_spec_limit(spec_limit, spec_metric) == expected


def test_badly_varying_deposits_never_read_marginal():
    assert bucket_magnitude(0.49, parse_spec_limit("500±50", "dot_diameter_um")) == "gross"


def test_profile_rejects_a_size_cv_spec_that_is_not_a_cv(client, catalog):
    response = client.post(
        "/api/profiles",
        json={
            "name": "Bad spec", "material_id": catalog["material"]["material_id"],
            "spec_metric": "size_cv", "spec_limit": "500±50", "geometry": sample_geometry(),
        },
    )
    assert response.status_code == 422


def test_diameter_spec_profile_still_flags_a_gross_spread(client, catalog):
    profile = client.post(
        "/api/profiles",
        json={
            "name": "Diameter spec", "material_id": catalog["material"]["material_id"],
            "spec_metric": "dot_diameter_um", "spec_limit": "500±50", "geometry": sample_geometry(),
        },
    ).json()
    case_id = open_case(client, {**catalog, "profile": profile})
    result = post_photo(client, case_id, photo_bytes("inconsistent"))
    assert result["magnitude"] == "gross"
    assert "size_varies" in result["suggested_signature"]
