"""Draws what the detector predicted onto the image itself -- colour-coded
right/wrong against that sample's own ground truth, with a text label per
dot showing the predicted tag(s) and, when wrong, the ground-truth tag(s)
too.

    .venv/bin/python -m detect.visualize --sample missing_carryover
    .venv/bin/python -m detect.visualize --all
    .venv/bin/python -m detect.visualize --all --mixed

Writes annotated PNGs to vision/detect/annotated/.

Colour key: green ring = matches expected.py's known-correct behaviour,
red ring = doesn't, teal ring = a class this pipeline can't judge yet
(air_bubble, satellite, contamination_speck -- see expected.py), yellow
dashed-looking ring = a detected blob with no matching profile position at
all (stray material).
"""

from __future__ import annotations

import argparse
import json
import pathlib

import cv2

from . import detect
from .expected import is_plausible

SAMPLES = pathlib.Path(__file__).resolve().parents[1] / "samples"
OUT = pathlib.Path(__file__).resolve().parent / "annotated"

CORRECT = (90, 200, 90)  # BGR: green
WRONG = (60, 60, 230)  # red
UNJUDGED = (180, 170, 60)  # teal
EXTRA = (0, 200, 230)  # yellow

TAG_ABBR = {
    "oversized": "OVER", "undersized": "UNDER", "irregular": "IRR",
    "misaligned": "MISALIGN", "missing": "MISS", "possibly_fused": "FUSED",
    "extra": "EXTRA",
}


def _abbr(tags: list[str]) -> str:
    return "+".join(TAG_ABBR.get(t, t) for t in tags) if tags else "ok"


def annotate_image(
    raw: bytes,
    result: dict,
    profile_data: dict | None = None,
) -> bytes:
    """Draws detection annotations onto the image bytes and returns PNG bytes.

    If ground-truth dots are present in profile_data (e.g. from synthetic samples),
    circles are colored by plausibility (green=plausible, red=divergent, teal=unjudged).
    When running without ground truth (e.g. real operational photos), nominal positions
    and detected defects are clearly annotated with green rings (or yellow for stray material).
    """
    import numpy as np

    arr = np.frombuffer(raw, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return b""

    # The recipe as detect() lined it up with this photo, when it reports
    # one — a registered photo's positions and radii are in its own pixels,
    # not the recipe's.
    prof_points = {}
    if result.get("positions"):
        prof_points = {p["index"]: p for p in result["positions"]}
    elif profile_data and "profile" in profile_data:
        prof_points = {p["index"]: p for p in profile_data["profile"]}

    gt_by_index = {}
    if profile_data and "dots" in profile_data:
        gt_by_index = {d["index"]: d for d in profile_data["dots"]}

    predicted_by_index = {d["index"]: d for d in result.get("dots", [])}

    indices = sorted(prof_points.keys()) if prof_points else [
        d["index"] for d in result.get("dots", []) if "index" in d
    ]

    for idx in indices:
        p = prof_points.get(idx, {})
        pred = predicted_by_index.get(idx, {})
        pred_tags = pred.get("tags", [])

        nominal_r = p.get("r", 26.0)
        radius = int(nominal_r) + 6

        # Use predicted coordinates if available; fall back to profile nominal
        cx = int(round(pred.get("cx", p.get("cx", 0))))
        cy = int(round(pred.get("cy", p.get("cy", 0))))

        if idx in gt_by_index:
            gt_tags = gt_by_index[idx].get("tags", [])
            verdict = is_plausible(gt_tags, pred_tags)
            if verdict is None:
                colour = UNJUDGED
            elif verdict:
                colour = CORRECT
            else:
                colour = WRONG
        else:
            colour = CORRECT

        cv2.circle(img, (cx, cy), radius, colour, 2)

        label = _abbr(pred_tags)
        if idx in gt_by_index and is_plausible(gt_by_index[idx].get("tags", []), pred_tags) is False:
            label += f"  (gt:{_abbr(gt_by_index[idx].get('tags', []))})"

        cv2.putText(
            img, label, (cx - radius, cy - radius - 6),
            cv2.FONT_HERSHEY_SIMPLEX, 0.38, colour, 1, cv2.LINE_AA,
        )

    for e in result.get("extra", []):
        cx, cy = int(round(e.get("cx", 0))), int(round(e.get("cy", 0)))
        cv2.circle(img, (cx, cy), 10, EXTRA, 2, cv2.LINE_AA)
        cv2.putText(
            img, "extra", (cx - 10, cy - 16),
            cv2.FONT_HERSHEY_SIMPLEX, 0.35, EXTRA, 1, cv2.LINE_AA,
        )

    ok, buf = cv2.imencode(".png", img)
    return buf.tobytes() if ok else b""


def annotate(name: str) -> pathlib.Path | None:
    json_path = SAMPLES / f"{name}.json"
    if not json_path.exists():
        json_path = SAMPLES / "mixed" / f"{name}.json"
    img_path = json_path.with_suffix(".png")
    if not json_path.exists() or not img_path.exists():
        print(f"skip {name}: not found")
        return None

    sidecar = json.loads(json_path.read_text())
    raw = img_path.read_bytes()
    result = detect(raw, sidecar)
    if "error" in result:
        print(f"skip {name}: {result['error']}")
        return None

    png_bytes = annotate_image(raw, result, sidecar)
    if not png_bytes:
        print(f"skip {name}: failed to annotate image {img_path}")
        return None

    OUT.mkdir(parents=True, exist_ok=True)
    out_path = OUT / f"{name}_annotated.png"
    out_path.write_bytes(png_bytes)
    rel = out_path.relative_to(SAMPLES.parent)

    predicted_by_index = {d["index"]: d for d in result.get("dots", [])}
    n_profile = len(sidecar.get("profile", []))
    counts = {"correct": 0, "wrong": 0, "unjudged": 0}

    for gt_dot in sidecar.get("dots", [])[:n_profile]:
        idx = gt_dot["index"]
        gt_tags = gt_dot["tags"]
        pred = predicted_by_index.get(idx, {"tags": []})
        verdict = is_plausible(gt_tags, pred.get("tags", []))

        if verdict is None:
            counts["unjudged"] += 1
        elif verdict:
            counts["correct"] += 1
        else:
            counts["wrong"] += 1

    print(f"{name:22} correct={counts['correct']:2} wrong={counts['wrong']:2} "
          f"unjudged={counts['unjudged']:2} extra={len(result.get('extra', [])):2}  -> {rel}")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", help="visualise one sample by name (e.g. missing_carryover)")
    parser.add_argument("--all", action="store_true", help="visualise every canonical sample")
    parser.add_argument("--mixed", action="store_true", help="with --all, also visualise the mixed set")
    args = parser.parse_args()

    if args.sample:
        annotate(args.sample)
        return

    if args.all:
        for p in sorted(SAMPLES.glob("*.json")):
            annotate(p.stem)
        if args.mixed:
            for p in sorted((SAMPLES / "mixed").glob("*.json")):
                annotate(p.stem)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
