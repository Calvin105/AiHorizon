from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.cases import crud as cases_crud
from app.domains.enums import RankTier
from app.domains.ranking import overrides
from app.domains.ranking.rule_map import rule_map
from app.domains.ranking.schema import RankingOut, RuleEditIn, RuleMapOut
from app.domains.ranking.service import run_ranking

router = APIRouter(prefix="/cases/{case_id}", tags=["Ranking (step 5)"])
rules_router = APIRouter(tags=["Ranking (step 5)"])


@router.post(
    "/rank",
    response_model=RankingOut,
    summary="Rank causes for a case",
    description=(
        "Runs both passes and both gates fresh over the case's current fingerprint, "
        "then stores and returns the result. Call this again after every step-6 check "
        "result — 'causes re-rank instantly' — and after step 3's vision analysis."
    ),
)
def rank(case_id: int, db: Session = Depends(get_db)) -> RankingOut:
    case = cases_crud.get_case(db, case_id)
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Case {case_id} not found")

    ranking = run_ranking(db, case)
    case.ranking = ranking
    case.rank_tier = RankTier(ranking["tier"])
    db.commit()
    return RankingOut(**ranking)


@rules_router.get(
    "/rules",
    response_model=RuleMapOut,
    summary="The rule table",
    description=(
        "Every answer, follow-up answer and photo measurement the rule engine knows, against "
        "every cause it moves, with its weight in log-odds and the page it cites; and every rule "
        "on its own, with the manual's weight next to the one in force. Read off the engine "
        "itself, so it is exactly what ranking applies."
    ),
)
def rules(db: Session = Depends(get_db)) -> RuleMapOut:
    return RuleMapOut(**asdict(rule_map(edits=overrides.saved(db))))


def _rule_or_404(rule_key: str):
    rule = overrides.find_rule(rule_key)
    if rule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No rule {rule_key!r}")
    return rule


_NEEDS_UPGRADE = (
    "This database predates rule editing. Run scripts/start-demo.sh --reset, "
    "or `uv run alembic upgrade head` in pipeline/backend."
)


@rules_router.put(
    "/rules/{rule_key}",
    response_model=RuleMapOut,
    summary="Change a rule's weight",
    description=(
        "Sets the weight in force, with the reason. Applies to every ranking from now on; "
        "cases already ranked keep their numbers until they are ranked again. Setting it "
        "back to the manual's weight is the same as restoring it."
    ),
)
def edit_rule(rule_key: str, body: RuleEditIn, db: Session = Depends(get_db)) -> RuleMapOut:
    rule = _rule_or_404(rule_key)
    try:
        overrides.save(db, rule, rule_key, body.weight, body.note.strip())
    except OperationalError as err:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, _NEEDS_UPGRADE) from err
    return rules(db)


@rules_router.delete(
    "/rules/{rule_key}",
    response_model=RuleMapOut,
    summary="Restore a rule to the manual's weight",
)
def restore_rule(rule_key: str, db: Session = Depends(get_db)) -> RuleMapOut:
    _rule_or_404(rule_key)
    try:
        overrides.restore(db, rule_key)
    except OperationalError as err:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, _NEEDS_UPGRADE) from err
    return rules(db)
