"""Slide-ready charts from evaluation/results/latest.json.

    uv run --with matplotlib python evaluation/plot.py

matplotlib is pulled in for this script only (`--with`), so it is not a
dependency of the app. Writes PNGs next to latest.json.
"""

from __future__ import annotations

import json
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS = pathlib.Path(__file__).resolve().parent / "results"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
BLUE = "#2a78d6"  # categorical slot 1
ORANGE = "#eb6834"  # categorical slot 2
GOOD, WARNING, CRITICAL, NEUTRAL = "#0ca30c", "#fab219", "#d03b3b", "#b9b8b3"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.facecolor": SURFACE,
    "figure.facecolor": SURFACE,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK_2,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.color": GRID,
    "grid.linewidth": 1,
    "axes.axisbelow": True,
})


def _title(fig, title: str, subtitle: str) -> None:
    fig.text(0.04, 0.95, title, fontsize=16, fontweight="bold", color=INK, va="top")
    fig.text(0.04, 0.885, subtitle, fontsize=11, color=INK_2, va="top")


def calibration(res: dict) -> None:
    rows = [r for r in res["diagnosis"]["calibration"]["by_stars"] if r["n"] >= 10]
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.subplots_adjust(top=0.78, bottom=0.14, left=0.1, right=0.96)
    xs = range(len(rows))
    ax.bar(xs, [r["accuracy"] * 100 for r in rows], width=0.6, color=BLUE)
    for x, r in zip(xs, rows, strict=True):
        ax.text(x, r["accuracy"] * 100 + 2, f"{r['accuracy'] * 100:.0f}%", ha="center", color=INK, fontsize=13,
                fontweight="bold")
    ax.set_xticks(list(xs), [f"{'★' * r['stars'] or '0 ★'}\n{r['n']} cases" for r in rows])
    ax.set_ylim(0, 110)
    ax.set_yticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylabel("Top cause was correct")
    _title(fig, "More stars, more often right",
           "Accuracy of the top-ranked cause at each confidence level shown to the operator\n"
           "(photo + questions, simulated cases, all operator-reliability levels)")
    fig.savefig(RESULTS / "calibration.png", dpi=200)
    plt.close(fig)


def reliability(res: dict) -> None:
    overall = res["diagnosis"]["overall"]
    levels = [1.0, 0.75, 0.5]
    series = [("Photo + questions", "photo_and_questions", BLUE), ("Questions only", "questions_only", ORANGE)]
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.subplots_adjust(top=0.78, bottom=0.14, left=0.1, right=0.8)
    xs = [lv * 100 for lv in levels]
    for label, key, colour in series:
        ys = [overall[f"{key}@{lv}"]["top1"] * 100 for lv in levels]
        ax.plot(xs, ys, color=colour, linewidth=2, marker="o", markersize=8,
                markeredgecolor=SURFACE, markeredgewidth=2)
        # x axis is reversed, so "- 2" is to the right of the last point
        ax.text(xs[-1] - 2, ys[-1], f"{label}\n{ys[-1]:.0f}%", color=INK, fontsize=11, va="center", ha="left")
        ax.annotate(f"{ys[0]:.0f}%", (xs[0], ys[0]), textcoords="offset points", xytext=(8, 6), color=INK_2,
                    fontsize=10)
    ax.axhline(100 / 7, color=INK_2, linewidth=1, linestyle=(0, (4, 4)))
    ax.text(99, 100 / 7 + 2, "Chance (1 in 7)", color=INK_2, fontsize=10, ha="left")
    ax.set_xlim(102, 48)  # more reliable on the left: reads as "as answers get worse"
    ax.set_xticks(xs, ["100%", "75%", "50%"])
    ax.set_xlabel("Share of operator answers that are right (the rest are random guesses)")
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylabel("Top cause correct")
    ax.legend([plt.Line2D([], [], color=c, linewidth=2, marker="o") for _, _, c in series],
              [s[0] for s in series], frameon=False, loc="upper right", fontsize=10)
    _title(fig, "The photo matters most when the answers are worst",
           f"Top-1 accuracy over {res['sizes']['cases_per_cause'] * 7} simulated cases per point")
    fig.savefig(RESULTS / "reliability.png", dpi=200)
    plt.close(fig)


def stress(res: dict) -> None:
    """Each damage at the level where it caused the most false alarms (the
    most severe level when none did) — the most severe level alone would
    hide a fault that is only unsafe when mild, like light board clutter,
    which heavier clutter turns into a safe refusal."""
    names = {"blur": "Blur", "noise": "Sensor noise", "uneven_light": "Uneven light", "glare": "Glare",
             "low_contrast": "Low contrast", "jpeg": "JPEG compression", "rotate": "Rotation", "shift": "Offset",
             "low_resolution": "Low resolution", "board_clutter": "Board clutter", "phone_photo": "Phone-photo mix"}
    levels = {"blur": "σ {} px", "noise": "σ {}", "uneven_light": "{} grey levels", "glare": "+{} grey levels",
              "low_contrast": "{} contrast", "jpeg": "quality {}", "rotate": "{}°", "shift": "{} px",
              "low_resolution": "{}× resolution", "board_clutter": "{} pads/traces", "phone_photo": "level {}"}
    rows = [("Undamaged", res["stress"]["clean"])]
    picked = []
    for key, v in res["stress"].items():
        if key == "clean":
            continue
        worst = max(enumerate(v["levels"]), key=lambda iv: (iv[1]["false_alarm"], iv[0]))[1]
        level = levels.get(key, "{}").format(f"{worst['level']:g}")
        label = f"{names.get(key, key)} · {level}"
        picked.append((label, worst))
    picked.sort(key=lambda kv: (kv[1]["false_alarm"], kv[1]["rejected"], -kv[1]["correct"]))  # safest first
    rows += picked
    unsafe = [label.split(" · ")[0].lower() for label, v in picked if v["false_alarm"] >= 0.05]
    parts = [("correct", "Correct", GOOD), ("rejected", "Refused (safe)", NEUTRAL),
             ("missed", "Missed", WARNING), ("false_alarm", "False alarm", CRITICAL)]

    fig, ax = plt.subplots(figsize=(10, 6.6))
    fig.subplots_adjust(top=0.8, bottom=0.16, left=0.31, right=0.97)
    ax.grid(False)
    ax.grid(True, axis="x", color=GRID)
    ys = list(range(len(rows)))[::-1]
    for y, (key, v) in zip(ys, rows, strict=True):
        left = 0.0
        for field, _label, colour in parts:
            w = v[field] * 100
            if w > 0:
                ax.barh(y, w, left=left, height=0.62, color=colour, edgecolor=SURFACE, linewidth=2)
            left += w
        if v["false_alarm"] >= 0.05:
            ax.text(101, y, f"{v['false_alarm'] * 100:.0f}% false alarm", va="center", fontsize=9, color=INK)
    ax.set_yticks(ys, [label for label, _ in rows])
    ax.get_yticklabels()[0].set_fontweight("bold")
    ax.set_xlim(0, 125)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.legend([plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in parts], [p[1] for p in parts],
              ncol=4, frameon=False, loc="upper left", bbox_to_anchor=(-0.02, -0.07), fontsize=10)
    remaining = (f"Only {' and '.join(unsafe)} still {'creates' if len(unsafe) == 1 else 'create'} false alarms."
                 if unsafe
                 else "No tested fault creates false alarms.")
    _title(fig, "What breaks the vision step",
           "Each photo fault at its least safe tested level, vs. the same images undamaged.\n" + remaining)
    fig.savefig(RESULTS / "stress.png", dpi=200)
    plt.close(fig)


def main() -> None:
    res = json.loads((RESULTS / "latest.json").read_text())
    calibration(res)
    reliability(res)
    stress(res)
    print(f"Wrote calibration.png, reliability.png, stress.png to {RESULTS}")


if __name__ == "__main__":
    main()
