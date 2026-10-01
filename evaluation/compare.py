"""Before/after table for two evaluation runs — the "results and
improvements achieved" evidence. Defaults to results/before_fixes.json
(the run before the 2026-09-29 vision fixes) against results/latest.json.

    uv run python evaluation/compare.py [before.json] [after.json] [out.md]

Writes results/before_after.md (or out.md) and prints it. A measure the
earlier run didn't have shows as "—" rather than failing the table.

    # the 2026-10-02 registration step, against the run just before it:
    uv run python evaluation/compare.py evaluation/results/before_registration.json \
        evaluation/results/latest.json evaluation/results/before_after_registration.md
"""

from __future__ import annotations

import json
import pathlib
import sys

RESULTS = pathlib.Path(__file__).resolve().parent / "results"


def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def _max_false_alarm(res: dict, damages: list[str]) -> float:
    return max(lv["false_alarm"] for d in damages for lv in res["stress"][d]["levels"])


def _worst_correct(res: dict, damages: list[str]) -> float | None:
    """The lowest correct rate over every level of these damages, or None
    when this run didn't test them."""
    if not all(d in res["stress"] for d in damages):
        return None
    return min(lv["correct"] for d in damages for lv in res["stress"][d]["levels"])


ROWS = [
    # (label, getter, higher_is_better)
    ("Irregular shapes detected", lambda r: r["measurement"]["irregular_shape"]["correct"], True),
    ("Undamaged photos measured correctly (all 5 conditions)", lambda r: r["stress"]["clean"]["correct"], True),
    ("Nozzle blockage ranked #1 (photo + questions, 75% reliable operator)",
     lambda r: r["diagnosis"]["per_cause"]["nozzle_blockage"]["top1"], True),
    ("Top cause correct — photo + questions, 75% reliable operator",
     lambda r: r["diagnosis"]["overall"]["photo_and_questions@0.75"]["top1"], True),
    ("Top cause correct — photo + questions, 50% reliable operator",
     lambda r: r["diagnosis"]["overall"]["photo_and_questions@0.5"]["top1"], True),
    ("Right when showing ★★★", lambda r: next(
        (s["accuracy"] for s in r["diagnosis"]["calibration"]["by_stars"] if s["stars"] == 3), 0.0), True),
    ("Worst false-alarm rate — glare / uneven light",
     lambda r: _max_false_alarm(r, ["glare", "uneven_light"]), False),
    ("Worst false-alarm rate — phone-photo mix", lambda r: _max_false_alarm(r, ["phone_photo"]), False),
    ("Worst false-alarm rate — board clutter", lambda r: _max_false_alarm(r, ["board_clutter"]), False),
    ("Photo 50 px off the recipe's position, measured correctly",
     lambda r: r["stress"]["shift"]["levels"][-1]["correct"], True),
    ("Phone-style framing measured correctly — worst of zoom 0.6-1.6x, off-centre, handheld",
     lambda r: _worst_correct(r, ["zoom", "reframe", "handheld"]), True),
]


def main() -> None:
    before_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else RESULTS / "before_fixes.json"
    after_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else RESULTS / "latest.json"
    out_path = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else RESULTS / "before_after.md"
    before, after = json.loads(before_path.read_text()), json.loads(after_path.read_text())

    lines = [f"# Before / after — {before['generated_at']} → {after['generated_at']}", "",
             "| Measure | Before | After | |", "|---|---|---|---|"]
    for label, get, higher_better in ROWS:
        b, a = get(before), get(after)
        if b is None or a is None:
            lines.append(f"| {label} | {'—' if b is None else _pct(b)} | {'—' if a is None else _pct(a)} | not tested before |")
            continue
        better = (a > b) if higher_better else (a < b)
        mark = "better" if better else ("same" if abs(a - b) < 0.005 else "**worse**")
        lines.append(f"| {label} | {_pct(b)} | {_pct(a)} | {mark} |")
    text = "\n".join(lines) + "\n"
    out_path.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
