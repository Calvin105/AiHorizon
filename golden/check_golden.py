#!/usr/bin/env python3
"""Sanity-checks every golden case under golden/.

Stdlib only, no imports from web/ or vision/ -- this folder stays a fixture
harness, not an app. Checks shapes against the real contracts (Answer/Signal
in web/core/types.ts, detect() in vision/detect/report.py) and that
signals.json's derived numbers actually follow from cv_output.json. It does
not call any reasoning engine -- there isn't one to call yet.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

GOLDEN_DIR = Path(__file__).parent
REQUIRED_FILES = [
    "user_input.json",
    "cv_output.json",
    "signals.json",
    "rag_output.json",
    "expected_reasoning.md",
]


def fail(case: str, msg: str) -> str:
    return f"[{case}] {msg}"


def check_user_input(case: str, data: dict) -> list[str]:
    errors = []
    answers = data.get("answers")
    if not isinstance(answers, list) or not answers:
        errors.append(fail(case, "user_input.json: 'answers' must be a non-empty list"))
        return errors
    for a in answers:
        for key in ("questionId", "prompt", "value"):
            if key not in a:
                errors.append(fail(case, f"user_input.json: answer missing '{key}'"))
    return errors


def check_cv_output(case: str, data: dict) -> list[str]:
    errors = []
    for key in ("profile_supplied", "summary", "dots", "extra", "counts"):
        if key not in data:
            errors.append(fail(case, f"cv_output.json: missing top-level key '{key}'"))
    summary = data.get("summary", {})
    for key in ("status", "dot_count", "flagged_count", "extra_count"):
        if key not in summary:
            errors.append(fail(case, f"cv_output.json: summary missing '{key}'"))
    dots = data.get("dots", [])
    for d in dots:
        for key in ("index", "cx", "cy", "tags"):
            if key not in d:
                errors.append(fail(case, f"cv_output.json: dot {d.get('index', '?')} missing '{key}'"))
    return errors


def check_signals(case: str, cv_output: dict, signals: list) -> list[str]:
    errors = []
    if not isinstance(signals, list) or not signals:
        errors.append(fail(case, "signals.json: must be a non-empty list"))
        return errors

    by_key = {}
    for s in signals:
        for key in ("key", "label", "value"):
            if key not in s:
                errors.append(fail(case, f"signals.json: entry missing '{key}'"))
        by_key[s.get("key")] = s.get("value")

    ratios = [d["area_ratio"] for d in cv_output.get("dots", []) if "area_ratio" in d]
    circs = [d["circularity"] for d in cv_output.get("dots", []) if "circularity" in d]

    if "size_cv" in by_key and ratios:
        mean = statistics.mean(ratios)
        pstdev = statistics.pstdev(ratios)
        expected_cv = pstdev / mean if mean else 0.0
        if abs(expected_cv - by_key["size_cv"]) > 0.005:
            errors.append(
                fail(case, f"signals.json: size_cv={by_key['size_cv']} does not match "
                           f"cv_output.json-derived value {expected_cv:.3f}")
            )

    if "mean_circularity" in by_key and circs:
        expected_mc = statistics.mean(circs)
        if abs(expected_mc - by_key["mean_circularity"]) > 0.005:
            errors.append(
                fail(case, f"signals.json: mean_circularity={by_key['mean_circularity']} does not match "
                           f"cv_output.json-derived value {expected_mc:.3f}")
            )
    return errors


def check_rag_output(case: str, data: dict) -> list[str]:
    errors = []
    passages = data.get("retrieved_passages")
    if not isinstance(passages, list) or not passages:
        errors.append(fail(case, "rag_output.json: 'retrieved_passages' must be a non-empty list"))
        return errors
    for p in passages:
        if "text" not in p or not p["text"]:
            errors.append(fail(case, "rag_output.json: a passage is missing 'text'"))
    if not data.get("synthesized_answer"):
        errors.append(fail(case, "rag_output.json: missing 'synthesized_answer'"))
    return errors


def check_case(case_dir: Path) -> list[str]:
    case = case_dir.name
    errors = []

    for filename in REQUIRED_FILES:
        if not (case_dir / filename).exists():
            errors.append(fail(case, f"missing required file '{filename}'"))
    if errors:
        return errors

    user_input = json.loads((case_dir / "user_input.json").read_text())
    cv_output = json.loads((case_dir / "cv_output.json").read_text())
    signals = json.loads((case_dir / "signals.json").read_text())
    rag_output = json.loads((case_dir / "rag_output.json").read_text())

    errors += check_user_input(case, user_input)
    errors += check_cv_output(case, cv_output)
    errors += check_signals(case, cv_output, signals)
    errors += check_rag_output(case, rag_output)
    return errors


def main() -> int:
    case_dirs = sorted(
        d for d in GOLDEN_DIR.iterdir()
        if d.is_dir() and (d / "user_input.json").exists()
    )
    if not case_dirs:
        print("No golden cases found under golden/.")
        return 1

    all_errors: list[str] = []
    for case_dir in case_dirs:
        errors = check_case(case_dir)
        all_errors += errors
        status = "FAIL" if errors else "OK"
        print(f"{status}  {case_dir.name}")

    for e in all_errors:
        print(f"  - {e}")

    if all_errors:
        print(f"\n{len(all_errors)} problem(s) across {len(case_dirs)} case(s).")
        return 1

    print(f"\nAll {len(case_dirs)} golden case(s) passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
