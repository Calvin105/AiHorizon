"""Evaluation runner. Three parts, each answering a question a judge asks:

  A. Measurement — put a known defect in the photo; does the vision step
     raise the signal the ranking relies on, and stay quiet on a good one?
  B. Diagnosis — photo + a simulated operator's answers; is the top cause
     right, and does the confidence shown (stars, %) track how often it is?
  C. Stress — damage the photo the way a real camera does; does the system
     stay right or refuse the image, rather than silently measure it wrong?

Everything runs through the real pipeline functions (run_vision,
rank_causes, compute_stars) — no API, no database, no LLM. Deterministic:
the same seeds give the same numbers.

    uv run python evaluation/run_eval.py            # full run, ~1-2 min
    uv run python evaluation/run_eval.py --quick    # smoke run

Writes evaluation/results/latest.json and evaluation/results/summary.md.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from common import ROOT, carryover_above_chance, make_image, measure
from degrade import DEGRADATIONS
from scenarios import PATTERNS, SCENARIOS, pick_image, simulate_answers

from app.domains.causes.vocabulary import load_causes
from app.domains.ranking.pass1 import rank_causes
from app.domains.report.stars import compute_stars

RESULTS = ROOT / "evaluation" / "results"
SPEC_CV = 0.15

# ---------------------------------------------------------------- part A --
# condition -> (defects, params, what "correct" means for it)

MEASURE_CONDITIONS: dict[str, tuple[list[str], dict, str]] = {
    "good": ([], {}, "no alarm: spread in spec, nothing missing, no irregular deposits, no carryover"),
    "carryover": (["missing_carryover"], {"missing_carryover": {"miss_rate": 0.2}},
                  "small-then-big pattern found above chance (p < 0.05)"),
    "scatter": (["inconsistent"], {"inconsistent": {"scale": (0.6, 1.45)}},
                "size spread out of spec, and NO false carryover pattern"),
    "missing_dots": (["ghost"], {"ghost": {"count": 2}},
                     "missing deposits counted, and NO false carryover pattern"),
    "irregular_shape": (["abnormal_shape"], {"abnormal_shape": {"count": 3}},
                        "irregular deposits counted (the blockage rule's trigger)"),
}


def verdict(condition: str, s: dict) -> str:
    """'correct', 'missed' (the defect's signal didn't fire — the ranking
    falls back on the interview, which is safe-ish), or 'false_alarm' (a
    signal fired that the image doesn't contain — this is what misleads).
    A false alarm outranks a miss when both happen."""
    carry = carryover_above_chance(s)
    cv, irregular, missing = s.get("size_cv", 0.0), s.get("irregular_count", 0), s.get("missing_count", 0)
    if condition == "good":
        return "correct" if cv <= SPEC_CV and missing == 0 and irregular == 0 and not carry else "false_alarm"
    if condition == "carryover":
        return "correct" if carry else "missed"
    if condition in ("scatter", "missing_dots"):
        if carry:
            return "false_alarm"
        fired = cv > SPEC_CV if condition == "scatter" else missing > 0
        return "correct" if fired else "missed"
    if condition == "irregular_shape":
        return "correct" if irregular > 0 else "missed"
    raise ValueError(condition)


OUTCOMES = ("correct", "rejected", "missed", "false_alarm")


def _measure_job(job: tuple) -> dict:
    condition, seed, pattern, degradation, level = job
    defects, params, _ = MEASURE_CONDITIONS[condition]
    img, geometry = make_image(pattern, defects, seed, params)
    if degradation:
        fn = DEGRADATIONS[degradation][0]
        img = fn(img, level, np.random.default_rng(seed + 991))
    v = measure(img, geometry)
    outcome = verdict(condition, v.signals) if v.quality_ok else "rejected"
    return {"condition": condition, "seed": seed, "pattern": pattern,
            "degradation": degradation, "level": level, "outcome": outcome}


def measurement_jobs(n: int, degradation: str | None = None, level: float | None = None) -> list[tuple]:
    return [
        (cond, 1000 + i, PATTERNS[i % len(PATTERNS)], degradation, level)
        for cond in MEASURE_CONDITIONS
        for i in range(n)
    ]


def summarise_outcomes(rows: list[dict]) -> dict:
    c = Counter(r["outcome"] for r in rows)
    n = len(rows)
    return {k: round(c[k] / n, 4) for k in OUTCOMES} | {"n": n}


# ---------------------------------------------------------------- part B --

RELIABILITIES = [1.0, 0.75, 0.5]
MODES = ["questions_only", "photo_only", "photo_and_questions"]


def _diagnosis_job(job: tuple) -> list[dict]:
    """One simulated case: one photo, measured once, then ranked under every
    mode x operator reliability. Same photo and same answer draws across
    modes, so the modes differ only in what evidence the ranking gets."""
    cause_idx, case_idx = job
    scenario = SCENARIOS[cause_idx]
    seed = 50_000 + cause_idx * 1000 + case_idx
    rng = np.random.default_rng(seed)
    recipe = pick_image(rng, scenario)
    pattern = PATTERNS[case_idx % len(PATTERNS)]
    img, geometry = make_image(pattern, recipe.defects, seed, recipe.params)
    v = measure(img, geometry)
    signals = v.signals if v.quality_ok else {}

    out = []
    for reliability in RELIABILITIES:
        axes = simulate_answers(np.random.default_rng(seed * 7 + int(reliability * 100)), scenario, reliability)
        for mode in MODES:
            if mode == "photo_only" and reliability != RELIABILITIES[0]:
                continue  # no answers involved; one copy is enough
            fp = {
                "axes": {} if mode == "photo_only" else axes,
                "signals": {} if mode == "questions_only" else signals,
            }
            ranked = rank_causes(fp)
            top, second = ranked[0], ranked[1]
            fired = sum(1 for r in ranked if r.evidence)
            ids = [r.cause_id for r in ranked]
            out.append({
                "cause": scenario.cause_id,
                "mode": mode,
                "reliability": None if mode == "photo_only" else reliability,
                "image": recipe.note,
                "quality_ok": v.quality_ok,
                "top": top.cause_id,
                "top_p": round(top.likelihood, 4),
                "second_p": round(second.likelihood, 4),
                "tied_top": abs(top.likelihood - second.likelihood) < 1e-9,
                "abstain": fired == 0,
                "true_rank": ids.index(scenario.cause_id) + 1,
                "stars": compute_stars(top.likelihood, second.likelihood, len(top.evidence)),
                "brier": sum((r.likelihood - (r.cause_id == scenario.cause_id)) ** 2 for r in ranked) / len(ranked),
            })
    return out


def summarise_diagnosis(rows: list[dict]) -> dict:
    n = len(rows)
    answered = [r for r in rows if not r["abstain"]]
    return {
        "n": n,
        "top1": round(sum(r["true_rank"] == 1 and not r["abstain"] for r in rows) / n, 4),
        "top3": round(sum(r["true_rank"] <= 3 and not r["abstain"] for r in rows) / n, 4),
        "abstain": round(sum(r["abstain"] for r in rows) / n, 4),
        "top1_when_answered": round(sum(r["true_rank"] == 1 for r in answered) / len(answered), 4) if answered else None,
        "tied_top": round(sum(r["tied_top"] and not r["abstain"] for r in rows) / n, 4),
        "brier": round(statistics.mean(r["brier"] for r in rows), 4),
        "mean_stars": round(statistics.mean(r["stars"] for r in rows), 2),
    }


def calibration(rows: list[dict]) -> dict:
    """Accuracy at each confidence level the operator is shown: by stars,
    and by the displayed top-cause percentage. Abstentions are excluded —
    'no cause is ahead' makes no claim to be right or wrong."""
    answered = [r for r in rows if not r["abstain"]]
    by_stars = defaultdict(list)
    for r in answered:
        by_stars[r["stars"]].append(r["true_rank"] == 1)
    bins = [(0.0, 0.4), (0.4, 0.55), (0.55, 0.7), (0.7, 0.85), (0.85, 1.01)]
    by_pct = []
    for lo, hi in bins:
        hits = [r["true_rank"] == 1 for r in answered if lo <= r["top_p"] < hi]
        mean_p = [r["top_p"] for r in answered if lo <= r["top_p"] < hi]
        by_pct.append({
            "bin": f"{int(lo * 100)}-{min(int(hi * 100), 100)}%",
            "n": len(hits),
            "mean_shown": round(statistics.mean(mean_p), 4) if mean_p else None,
            "accuracy": round(sum(hits) / len(hits), 4) if hits else None,
        })
    return {
        "by_stars": [
            {"stars": s, "n": len(v), "accuracy": round(sum(v) / len(v), 4)} for s, v in sorted(by_stars.items())
        ],
        "by_percent": by_pct,
    }


def confusion(rows: list[dict]) -> dict:
    table: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        table[r["cause"]]["(no cause ahead)" if r["abstain"] else r["top"]] += 1
    return {k: dict(v) for k, v in table.items()}


# ------------------------------------------------------------------ main --

def pct(x: float | None) -> str:
    return "—" if x is None else f"{x * 100:.0f}%"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="small n, for checking the runner itself")
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args()
    n_measure, n_stress, n_cases = (6, 3, 8) if args.quick else (40, 20, 60)

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        # A
        a_rows = list(pool.map(_measure_job, measurement_jobs(n_measure), chunksize=8))
        # B
        b_jobs = [(ci, k) for ci in range(len(SCENARIOS)) for k in range(n_cases)]
        b_rows = [row for rows in pool.map(_diagnosis_job, b_jobs, chunksize=8) for row in rows]
        # C
        c_jobs = [
            job
            for name, (_fn, levels, _unit) in DEGRADATIONS.items()
            for level in levels
            for job in measurement_jobs(n_stress, name, level)
        ]
        c_rows = list(pool.map(_measure_job, c_jobs, chunksize=16))

    # ---- aggregate
    part_a = {
        cond: summarise_outcomes([r for r in a_rows if r["condition"] == cond]) | {"means": desc}
        for cond, (_d, _p, desc) in MEASURE_CONDITIONS.items()
    }
    part_a["all"] = summarise_outcomes(a_rows)
    by_pattern = {
        cond: {p: summarise_outcomes([r for r in a_rows if r["condition"] == cond and r["pattern"] == p])
               for p in PATTERNS}
        for cond in MEASURE_CONDITIONS
    }

    part_b: dict = {"overall": {}, "per_cause": {}, "calibration": {}, "confusion": {}}
    for mode in MODES:
        for rel in (RELIABILITIES if mode != "photo_only" else [None]):
            key = mode if rel is None else f"{mode}@{rel}"
            rows = [r for r in b_rows if r["mode"] == mode and r["reliability"] == rel]
            part_b["overall"][key] = summarise_diagnosis(rows)
    headline = [r for r in b_rows if r["mode"] == "photo_and_questions" and r["reliability"] == 0.75]
    for cause in [c["id"] for c in load_causes()]:
        part_b["per_cause"][cause] = summarise_diagnosis([r for r in headline if r["cause"] == cause])
    part_b["calibration"] = calibration([r for r in b_rows if r["mode"] == "photo_and_questions"])
    part_b["confusion"] = confusion(headline)

    # Stress images are the first n_stress seeds of part A's, so part A's
    # rows on those seeds are the undamaged baseline for every damage row.
    stress_seeds = {job[1] for job in measurement_jobs(n_stress)}
    part_c: dict = {"clean": summarise_outcomes([r for r in a_rows if r["seed"] in stress_seeds])}
    for name, (_fn, levels, unit) in DEGRADATIONS.items():
        part_c[name] = {
            "unit": unit,
            "levels": [
                {"level": lv} | summarise_outcomes([r for r in c_rows if r["degradation"] == name and r["level"] == lv])
                for lv in levels
            ],
        }

    results = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M"),
        "quick": args.quick,
        "seconds": round(time.time() - t0, 1),
        "sizes": {"measurement_per_condition": n_measure, "stress_per_condition_per_level": n_stress,
                  "cases_per_cause": n_cases},
        "measurement": part_a,
        "measurement_by_pattern": by_pattern,
        "diagnosis": part_b,
        "stress": part_c,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "latest.json").write_text(json.dumps(results, indent=2))
    summary = render_summary(results)
    (RESULTS / "summary.md").write_text(summary)
    print(summary)


def render_summary(res: dict) -> str:
    L: list[str] = []
    s = res["sizes"]
    L += [f"# Evaluation — {res['generated_at']}{' (QUICK)' if res['quick'] else ''}", "",
          (f"Ran in {res['seconds']}s. All images synthetic (vision/synth), all operator answers simulated "
          "(evaluation/scenarios.py, team judgement). No API, no database, no LLM."), ""]

    L += ["## A. Measurement — does the photo raise the right signal?", "",
          f"{s['measurement_per_condition']} images per condition, spread over {len(PATTERNS)} dispense patterns.", "",
          ("**Missed** = the defect's signal didn't fire, so ranking leans on the interview. "
          "**False alarm** = a signal fired that the image doesn't contain — the outcome that misleads."), "",
          "| Condition | Correct | Refused | Missed | False alarm | Correct means |",
          "|---|---|---|---|---|---|"]
    for cond, v in res["measurement"].items():
        if cond == "all":
            continue
        L.append(f"| {cond} | {pct(v['correct'])} | {pct(v['rejected'])} | {pct(v['missed'])} | "
                 f"{pct(v['false_alarm'])} | {v['means']} |")
    L += ["", "Correct, by dispense pattern:", "",
          "| Condition | " + " | ".join(PATTERNS) + " |", "|---|" + "---|" * len(PATTERNS)]
    for cond, pats in res["measurement_by_pattern"].items():
        L.append(f"| {cond} | " + " | ".join(pct(pats[p]["correct"]) for p in PATTERNS) + " |")
    L.append("")

    d = res["diagnosis"]
    L += ["## B. Diagnosis — is the top cause right?", "",
          (f"{s['cases_per_cause']} simulated cases per cause x 7 causes. *Reliability* = chance each answer "
          "comes from the scenario card rather than a random guess."), "",
          "| Evidence given | Top-1 | In top 3 | 'No cause ahead' | Top-1 when it named one | Brier (lower=better) |",
          "|---|---|---|---|---|---|"]
    for key, v in d["overall"].items():
        L.append(f"| {key} | {pct(v['top1'])} | {pct(v['top3'])} | {pct(v['abstain'])} | "
                 f"{pct(v['top1_when_answered'])} | {v['brier']} |")
    L += ["", "Chance level for top-1 is 14% (1 in 7).", "",
          "### Per cause (photo + questions, reliability 0.75)", "",
          "| True cause | Top-1 | In top 3 | 'No cause ahead' |", "|---|---|---|---|"]
    for cause, v in d["per_cause"].items():
        L.append(f"| {cause} | {pct(v['top1'])} | {pct(v['top3'])} | {pct(v['abstain'])} |")
    L += ["", "### What it picked instead (photo + questions, reliability 0.75)", ""]
    for cause, picks in d["confusion"].items():
        ranked = ", ".join(f"{k} {v}" for k, v in sorted(picks.items(), key=lambda kv: -kv[1]))
        L.append(f"- **{cause}** → {ranked}")
    L += ["", "### Calibration — when it is confident, is it right? (photo + questions, all reliabilities)", "",
          "| Stars shown | Cases | Top-1 accuracy |", "|---|---|---|"]
    for row in d["calibration"]["by_stars"]:
        L.append(f"| {'★' * row['stars'] or '0'} | {row['n']} | {pct(row['accuracy'])} |")
    L += ["", "| Top cause shown at | Cases | Mean shown | Actually right |", "|---|---|---|---|"]
    for row in d["calibration"]["by_percent"]:
        L.append(f"| {row['bin']} | {row['n']} | {pct(row['mean_shown'])} | {pct(row['accuracy'])} |")
    L.append("")

    L += ["## C. Stress — damaged photos", "",
          (f"{s['stress_per_condition_per_level']} images per condition per level, all 5 measurement conditions. "
          "Compare each row with the **undamaged** row: that gap is what the damage cost. "
          "Refusing is the safe failure; a rise in false alarms is the unsafe one."), "",
          "| Damage | Level | Correct | Refused | Missed | False alarm |", "|---|---|---|---|---|---|"]
    clean = res["stress"]["clean"]
    L.append(f"| **undamaged** | — | {pct(clean['correct'])} | {pct(clean['rejected'])} | {pct(clean['missed'])} | "
             f"{pct(clean['false_alarm'])} |")
    for name, v in res["stress"].items():
        if name == "clean":
            continue
        for row in v["levels"]:
            L.append(f"| {name} | {row['level']} {v['unit']} | {pct(row['correct'])} | {pct(row['rejected'])} | "
                     f"{pct(row['missed'])} | {pct(row['false_alarm'])} |")
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    main()
