"""Runs vision/detect against every canonical AND mixed sample and reports,
for each generator-assigned class, what symptom(s) the detector actually
predicted.

This is a coverage report, not a pass/fail gate: several generator classes
share a symptom by design (see classify.py's docstring), and some are known
not to be detectable from silhouette alone yet. Read the breakdown rather
than expecting every row to show one clean answer.

    .venv/bin/python -m detect.evaluate
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter

from . import detect

SAMPLES = pathlib.Path(__file__).resolve().parents[1] / "samples"


def _iter_sidecars():
    yield from sorted(SAMPLES.glob("*.json"))
    mixed = SAMPLES / "mixed"
    if mixed.is_dir():
        yield from sorted(mixed.glob("*.json"))


def main() -> None:
    coverage: dict[str, Counter] = {}
    extra_blobs_total = 0
    n_images = 0

    for json_path in _iter_sidecars():
        sidecar = json.loads(json_path.read_text())
        img_path = json_path.with_suffix(".png")
        if not img_path.exists():
            continue
        result = detect(img_path.read_bytes(), sidecar)
        if "error" in result:
            continue
        n_images += 1
        extra_blobs_total += len(result.get("extra", []))

        predicted_by_index = {d["index"]: d["tags"] for d in result["dots"]}
        n_profile = len(sidecar["profile"])
        for gt_dot in sidecar["dots"][:n_profile]:
            idx = gt_dot["index"]
            gt_tags = gt_dot["tags"] or ["good"]
            predicted = predicted_by_index.get(idx, [])
            for gt_tag in gt_tags:
                bucket = coverage.setdefault(gt_tag, Counter())
                if predicted:
                    for pt in predicted:
                        bucket[pt] += 1
                else:
                    bucket["(nothing flagged)"] += 1

    n_instances = sum(sum(bucket.values()) for bucket in coverage.values())
    print(f"Ran detect() with a profile against {n_images} images ({n_instances} labelled dot-instances).\n")
    print(f"{'generator tag':22} n     predicted symptom breakdown")
    print("-" * 78)
    for gt_tag in sorted(coverage):
        total = sum(coverage[gt_tag].values())
        breakdown = ", ".join(f"{k}={v}" for k, v in coverage[gt_tag].most_common())
        print(f"{gt_tag:22} {total:<5} {breakdown}")

    print(f"\nExtra (unmatched) blobs across all images: {extra_blobs_total}")
    print("(covers contamination specks and satellites that cleared the area-noise floor)")


if __name__ == "__main__":
    main()
