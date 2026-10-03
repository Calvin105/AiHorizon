from typing import Literal

from pydantic import BaseModel


class EvidenceOut(BaseModel):
    label: str
    detail: str
    source: str
    weight: float
    kind: str


class Pass1CauseOut(BaseModel):
    cause_id: str
    label: str
    likelihood: float
    evidence: list[EvidenceOut]


class Pass2CauseOut(BaseModel):
    cause_id: str
    likelihood_pct: float


class GateAOut(BaseModel):
    above_chance: bool
    deciding_signal: str | None
    p_value: float | None
    note: str


class GateBOut(BaseModel):
    applied: bool
    matched_count: int
    contradicting_count: int
    note: str


class RankingOut(BaseModel):
    pass1: list[Pass1CauseOut]
    pass2: list[Pass2CauseOut] | None
    agree: bool
    critic_top_cause_id: str | None = None
    """The critic's pick, or null when it abstained — see pass2.critic_verdict.
    Null with a non-empty `pass2` means it ranked the causes but had no
    clear view, which is not counted as disagreement."""
    critic_note: str = ""
    """Why the critic did or didn't get a vote, in words the UI can show."""
    gate_a: GateAOut
    gate_b: GateBOut
    tier: str
    top_cause_id: str
    runners_up: list[str]


class RuleCellOut(BaseModel):
    cause_id: str
    weight: float
    """Log-odds. For a photo measurement, the weight at full strength."""
    weight_mild: float | None = None
    """Photo measurements only: the weight just past normal."""
    label: str
    detail: str
    source: str


class EvidenceRowOut(BaseModel):
    id: str
    label: str
    help: str
    mild_text: str | None = None
    strong_text: str | None = None
    excludes: list[str] = []
    """Rows that can't count at the same time as this one."""
    cells: list[RuleCellOut]
    """Empty when the answer adds no evidence either way."""


class EvidenceGroupOut(BaseModel):
    id: str
    kind: Literal["measured", "question", "followup"]
    title: str
    prompt: str
    note: str
    single: bool
    """One answer at a time, as the question is asked."""
    rows: list[EvidenceRowOut]


class CauseColumnOut(BaseModel):
    cause_id: str
    label: str
    rule_count: int


class RuleMapOut(BaseModel):
    prior: float
    rule_count: int
    check_confirms: float
    check_rules_out: float
    causes: list[CauseColumnOut]
    groups: list[EvidenceGroupOut]
