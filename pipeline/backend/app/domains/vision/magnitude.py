"""DESIGN.md W3: "Magnitude is computed from the signals, not asked."
Buckets how far size_cv sits past its spec limit — the operator is never
asked to estimate what the image already measures."""

import re

DEFAULT_SPEC_LIMIT = 0.15  # DESIGN.md's own worked example: "size_cv < 0.15"
SIZE_CV_METRICS = (None, "", "size_cv")

_CV_LIMIT = re.compile(r"\s*(?:<=?|≤)?\s*(\d*\.?\d+)\s*")


def parse_spec_limit(spec_limit: str | None, spec_metric: str | None = "size_cv") -> float:
    """The size_cv limit a profile's spec states, or DEFAULT_SPEC_LIMIT when
    it states none.

    Only a size-spread spec counts. This used to take the first number in
    any string, so a dot-diameter tolerance of "500±50" became a size_cv
    limit of 500: every photo then read "marginal" and every re-measurement
    passed as in spec. A coefficient of variation lives between 0 and 1, so
    anything else falls back to the default rather than being trusted."""
    if spec_metric not in SIZE_CV_METRICS or not spec_limit:
        return DEFAULT_SPEC_LIMIT
    match = _CV_LIMIT.fullmatch(spec_limit)
    if not match:
        return DEFAULT_SPEC_LIMIT
    value = float(match.group(1))
    return value if 0 < value <= 1 else DEFAULT_SPEC_LIMIT


def is_size_cv_spec(spec_limit: str) -> bool:
    """Whether a spec string reads as a size_cv limit at all — for refusing a
    profile that claims a size_cv metric with some other kind of number."""
    match = _CV_LIMIT.fullmatch(spec_limit)
    return bool(match) and 0 < float(match.group(1)) <= 1


def bucket_magnitude(size_cv: float | None, limit: float = DEFAULT_SPEC_LIMIT) -> str:
    if size_cv is None:
        return "unknown"

    ratio = size_cv / limit if limit else 0.0

    if ratio <= 1.0:
        return "marginal"
    if ratio <= 2.0:
        return "moderate"
    if ratio <= 3.5:
        return "gross"
    return "total-failure"
