"""What backs the top cause: how many of the reasons the ranking lists for
it push it up, and where each one came from.

This is what the app shows in place of the star rating it used to give the
diagnosis. Stars read as a confidence level, and they mixed two things --
how many reasons there were, and how far #1 led #2 -- into a number nobody
could trace. A count of reasons can be checked against the "Why?" list, and
the evaluation measures it: in evaluation/results/summary.md, the more
reasons back the top cause, the more often it is right.

The tier is the confidence the app states. This is the evidence under it.
"""

from collections import Counter
from collections.abc import Iterable
from typing import Any


def _get(evidence: Any, key: str) -> Any:
    return evidence[key] if isinstance(evidence, dict) else getattr(evidence, key)


def backing(evidence: Iterable[Any]) -> dict:
    """Takes a cause's evidence -- RuleHit objects, or their stored dicts.

    A reason is one rule that fired for the cause with a positive weight,
    or one check that confirmed it. `measured`, `answers` and `checks` split
    the reasons by where they came from; `against` counts what fired the
    other way."""
    items = list(evidence)
    supporting = [e for e in items if _get(e, "weight") > 0]
    kinds = Counter(_get(e, "kind") for e in supporting)
    return {
        "reasons": len(supporting),
        "measured": kinds["signal"],
        "answers": kinds["answer"],
        "checks": kinds["check"],
        "against": sum(1 for e in items if _get(e, "weight") < 0),
    }
