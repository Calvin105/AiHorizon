"""Before/after table for two evaluation runs — the "results and
improvements achieved" evidence. Defaults to results/before_fixes.json
(the run before the 2026-09-29 vision fixes) against results/latest.json.

    uv run python evaluation/compare.py [before.json] [after.json]

Writes results/before_after.md and prints it.
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
]


def main() -> None:
    before_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else RESULTS / "before_fixes.json"
    after_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else RESULTS / "latest.json"
    before, after = json.loads(before_path.read_text()), json.loads(after_path.read_text())

    lines = [f"# Before / after — {before['generated_at']} → {after['generated_at']}", "",
             "| Measure | Before | After | |", "|---|---|---|---|"]
    for label, get, higher_better in ROWS:
        b, a = get(before), get(after)
        better = (a > b) if higher_better else (a < b)
        mark = "better" if better else ("same" if abs(a - b) < 0.005 else "**worse**")
        lines.append(f"| {label} | {_pct(b)} | {_pct(a)} | {mark} |")
    text = "\n".join(lines) + "\n"
    (RESULTS / "before_after.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
