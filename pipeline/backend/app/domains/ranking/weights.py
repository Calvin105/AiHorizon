"""The weight each rule carries right now: the manual's (rules.py) unless an
engineer changed it on the rules page.

Applied wherever a rule is evaluated (ranking, the cause comparison, the
rule table), so one edit changes all of them at once. The rule_overrides
table is the record, with the reason in its note; ranking/overrides.py
loads it into this module at startup and after every edit. Nothing here
touches the database, so the evaluation harness, which never loads it,
always measures the manual's weights.
"""

import re

from app.domains.ranking.rules import CauseRule, Fingerprint

_in_force: dict[str, float] = {}


def rule_key(cause_id: str, rule: CauseRule) -> str:
    """A rule's stable id: its cause and its label, slugged."""
    return f"{cause_id}:{re.sub(r'[^a-z0-9]+', '-', rule.label.lower()).strip('-')}"


def replace_all(edited: dict[str, float]) -> None:
    _in_force.clear()
    _in_force.update(edited)


def edited_weight(key: str) -> float | None:
    """The weight an engineer set for this rule, or None for the manual's."""
    return _in_force.get(key)


def is_edited(cause_id: str, rule: CauseRule) -> bool:
    return bool(_in_force) and rule_key(cause_id, rule) in _in_force


def weigh(cause_id: str, rule: CauseRule, fingerprint: Fingerprint) -> float | None:
    """The rule's contribution in log-odds at the weight in force. A signal
    rule keeps its ramp: an edit rescales it rather than flattening it."""
    contribution = rule.evaluate(fingerprint)
    if contribution is None or not _in_force:
        return contribution
    weight = _in_force.get(rule_key(cause_id, rule))
    if weight is None:
        return contribution
    if weight == 0:
        return None  # switched off
    return contribution * weight / rule.evaluate.weight
