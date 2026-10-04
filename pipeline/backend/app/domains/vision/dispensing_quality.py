"""The brief's Bonus 2, "AI Dispensing Quality Score": how good the deposits
in the photo are, as the brief lays it out -- a star rating per aspect and
an overall score out of 100.

It rates the dispensing, not the diagnosis. How far the ranking can be
trusted is the tier's job, with the reasons that back it; this only says
what the photo measured.

Every number is a count of deposits, so each rating can be checked by eye
on the annotated photo:

- Completeness: deposits present, of every position in the recipe.
- Size consistency: present deposits within SIZE_TOLERANCE of the nominal
  area, the same 15% the vision step uses to mark one off-size.
- Shape consistency: present deposits that measured round.
- Dispensing position: present deposits where the recipe put them.

An aspect earns floor(5 x share) stars, so a single failure always costs a
star. The overall score is the share of positions whose deposit passed all
four, out of 100.
"""

from detect.classify import SIZE_TOLERANCE

ASPECTS = (
    ("completeness", "Completeness"),
    ("size", "Size consistency"),
    ("shape", "Shape consistency"),
    ("position", "Dispensing position"),
)


def _stars(passed: int, total: int) -> int:
    return 5 * passed // total if total else 0


def rate_dispensing(cv_output: dict) -> dict | None:
    """None when there is nothing to rate: no recipe positions measured."""
    dots = cv_output.get("dots", [])
    if not dots:
        return None
    present = [d for d in dots if "area_ratio" in d]

    checks = {
        "size": lambda d: abs(d["area_ratio"] - 1) <= SIZE_TOLERANCE,
        "shape": lambda d: "irregular" not in d["tags"],
        "position": lambda d: "misaligned" not in d["tags"],
    }
    passed = {key: sum(1 for d in present if ok(d)) for key, ok in checks.items()}
    passed["completeness"] = len(present)
    totals = {"completeness": len(dots), "size": len(present), "shape": len(present), "position": len(present)}
    details = {
        "completeness": f"{len(present)} of {len(dots)} deposits present",
        "size": f"{passed['size']} of {len(present)} within {round(SIZE_TOLERANCE * 100)}% of the nominal size",
        "shape": f"{passed['shape']} of {len(present)} round",
        "position": f"{passed['position']} of {len(present)} where the recipe puts them",
    }
    good = sum(1 for d in present if all(ok(d) for ok in checks.values()))

    return {
        "aspects": [
            {
                "key": key, "label": label, "stars": _stars(passed[key], totals[key]),
                "passed": passed[key], "total": totals[key], "detail": details[key],
            }
            for key, label in ASPECTS
        ],
        "overall": round(100 * good / len(dots)),
        "passed": good,
        "total": len(dots),
        "detail": f"{good} of {len(dots)} deposits passed all four",
    }
