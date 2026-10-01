"""Step 5b — fine case retrieval, and ranking/gates.py's Gate B. Key: the
full signal vector. CONFIRMED cases only. Can demote, never promote.

Deliberately not sharing anything with retrieval/coarse.py: this matches
by numeric distance over signals, not categorical axis agreement, and a
signal sitting at its chance level carries no weight here for the same
reason it carries none in the ranking gate itself.

Two limits keep "precedent" meaning a similar problem. DESIGN.md's hard
filter comes first — same material family and dispenser class, the same
key step 2b uses. Then a case only matches when its signals sit within
MAX_DISTANCE: this used to return the ten *nearest* confirmed cases however
far away they were, so every confirmed case on file "matched", and Gate B
demoted causes on the strength of unrelated problems.
"""

import statistics
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.cases.model import Case
from app.domains.enums import CaseTier
from app.domains.materials.model import FluidMaterial
from app.domains.profiles.model import DispenseProfile
from app.domains.stations.model import DispenseStation

CHANCE_KEYS_SUFFIX = "_chance_p"
MAX_DISTANCE = 1.0
"""Mean distance over the shared signals, each in units of its own spread
across the confirmed cases. Further than one spread on average is a
different problem, not a precedent."""


@dataclass
class FineMatch:
    case_id: int
    distance: float
    cause_id: str | None


def _signal_spread(values: list[float]) -> float:
    if len(values) < 2:
        return 1.0
    spread = statistics.pstdev(values)
    return spread if spread > 1e-9 else 1.0


def _at_chance(signals: dict, key: str) -> bool:
    p = signals.get(f"{key}{CHANCE_KEYS_SUFFIX}")
    return isinstance(p, int | float) and p >= 0.05


def fine_match(db: Session, case: Case, *, limit: int = 10) -> list[FineMatch]:
    fingerprint = case.fingerprint or {}
    query = (
        select(Case)
        .join(DispenseStation, Case.station_id == DispenseStation.station_id)
        .join(DispenseProfile, Case.profile_id == DispenseProfile.profile_id)
        .join(FluidMaterial, DispenseProfile.material_id == FluidMaterial.material_id)
        .where(Case.tier == CaseTier.CONFIRMED)
        .where(DispenseStation.dispenser_class == case.station.dispenser_class)
        .where(FluidMaterial.family == case.profile.material.family)
    )
    # (case, its fingerprint) pairs, fingerprint narrowed to non-None here
    # so nothing downstream has to re-check it.
    confirmed = [(c, c.fingerprint) for c in db.scalars(query) if c.case_id != case.case_id and c.fingerprint]
    if not confirmed:
        return []

    my_signals = fingerprint.get("signals", {})
    discriminating_keys = [
        k for k in my_signals
        if isinstance(my_signals[k], int | float)
        and not k.endswith(CHANCE_KEYS_SUFFIX)
        and not _at_chance(my_signals, k)
    ]
    if not discriminating_keys:
        return []

    spreads = {
        key: _signal_spread(
            [fp["signals"][key] for _, fp in confirmed if key in fp.get("signals", {})]
        )
        for key in discriminating_keys
    }

    results: list[FineMatch] = []
    for past, fp in confirmed:
        their_signals = fp.get("signals", {})
        shared = [k for k in discriminating_keys if isinstance(their_signals.get(k), int | float)]
        if not shared:
            continue
        distance = statistics.mean(
            abs(my_signals[k] - their_signals[k]) / spreads[k] for k in shared
        )
        if distance > MAX_DISTANCE:
            continue
        cause_id = (past.diagnosis or {}).get("cause_id")
        results.append(FineMatch(case_id=past.case_id, distance=round(distance, 3), cause_id=cause_id))

    return sorted(results, key=lambda m: m.distance)[:limit]
