"""Step 3 must persist what it measured — every time, not just the first."""

import cv2
import numpy as np

from tests.conftest import open_case, photo_bytes, post_photo


def _signals(client, case_id: int) -> dict:
    return client.get(f"/api/cases/{case_id}").json()["fingerprint"]["signals"]


def _unalignable(name: str) -> bytes:
    """The sample's frame wiped blank: nothing to measure, so the quality
    gate refuses it — the photo an operator is then told to retake."""
    img = cv2.imdecode(np.frombuffer(photo_bytes(name), np.uint8), cv2.IMREAD_COLOR)
    img[:, :] = 255
    return cv2.imencode(".png", img)[1].tobytes()


def test_retake_after_a_refused_photo_keeps_its_measurements(client, catalog):
    case_id = open_case(client, catalog)
    refused = post_photo(client, case_id, _unalignable("inconsistent"))
    assert refused["quality_ok"] is False

    retake = post_photo(client, case_id, photo_bytes("inconsistent"))
    assert retake["quality_ok"] is True

    stored = _signals(client, case_id)
    assert stored["size_cv"] == retake["signals"]["size_cv"]


def test_a_new_photo_replaces_the_last_photos_signals(client, catalog):
    case_id = open_case(client, catalog)
    post_photo(client, case_id, photo_bytes("missing_carryover"))
    assert "small_then_big_chance_p" in _signals(client, case_id)

    post_photo(client, case_id, photo_bytes("good"))
    stored = _signals(client, case_id)
    assert stored["size_cv"] < 0.15
    # A carryover p-value from the earlier image must not survive next to
    # measurements it was never taken with.
    assert "small_then_big_chance_p" not in stored


def test_image_only_signature_follows_the_latest_photo(client, catalog):
    case_id = open_case(client, catalog)
    post_photo(client, case_id, photo_bytes("missing_carryover"))
    axes = client.get(f"/api/cases/{case_id}").json()["fingerprint"]["axes"]
    assert "small_then_big" in axes["signature"]

    post_photo(client, case_id, photo_bytes("good"))
    axes = client.get(f"/api/cases/{case_id}").json()["fingerprint"]["axes"]
    assert "small_then_big" not in axes["signature"]


def test_a_photo_framed_unlike_the_recipe_is_still_measured(client, catalog):
    # Closer, off-centre and slightly turned: how a phone photo of the same
    # board actually arrives. It used to be refused as "board features".
    img = cv2.imdecode(np.frombuffer(photo_bytes("inconsistent"), np.uint8), cv2.IMREAD_COLOR)
    h, w = img.shape[:2]
    img = cv2.warpAffine(img, cv2.getRotationMatrix2D((w / 2, h / 2), 5, 1.0), (w, h), borderValue=(255, 255, 255))
    img = cv2.copyMakeBorder(img, 90, 30, 140, 20, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    img = cv2.resize(img, None, fx=1.4, fy=1.4)
    case_id = open_case(client, catalog)

    result = post_photo(client, case_id, cv2.imencode(".png", img)[1].tobytes())
    assert result["quality_ok"] is True
    assert abs(result["signals"]["size_cv"] - 0.486) < 0.02
    assert result["cv_output"]["registration"]["applied"] is True


def test_a_photo_framed_like_the_recipe_is_not_registered(client, catalog):
    case_id = open_case(client, catalog)
    result = post_photo(client, case_id, photo_bytes("misaligned"))
    # A pattern dispensed off-position must stay a finding, not be lined up away.
    assert result["cv_output"]["registration"]["applied"] is False


def test_interview_answers_survive_a_photo(client, catalog):
    case_id = open_case(client, catalog)
    client.patch(
        f"/api/cases/{case_id}",
        json={"fingerprint": {"axes": {"signature": ["size_varies"], "trajectory": "random"}}},
    )
    post_photo(client, case_id, photo_bytes("inconsistent"))
    case = client.get(f"/api/cases/{case_id}").json()
    assert case["fingerprint"]["axes"]["trajectory"] == "random"
    assert case["fingerprint"]["signals"]["size_cv"] > 0.15
