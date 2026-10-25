from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import RiskAssessment, Transaction
from app.schemas.assessment import AlertPage, AssessmentRead

router = APIRouter(tags=["risk"])


@router.get("/alerts", response_model=AlertPage)
def list_alerts(
    session: Annotated[Session, Depends(get_db)],
    severity: Literal["low", "medium", "high", "critical"] | None = None,
    min_score: Annotated[int | None, Query(ge=0, le=100)] = None,
    max_score: Annotated[int | None, Query(ge=0, le=100)] = None,
    review_status: Literal["open", "reviewed", "dismissed"] | None = None,
    search: Annotated[str | None, Query(min_length=1, max_length=256)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AlertPage:
    query = select(RiskAssessment, Transaction).join(Transaction, Transaction.id == RiskAssessment.transaction_id)
    filters = []
    if severity is not None:
        filters.append(RiskAssessment.severity == severity)
    if min_score is not None:
        filters.append(RiskAssessment.risk_score >= min_score)
    if max_score is not None:
        filters.append(RiskAssessment.risk_score <= max_score)
    if review_status is not None:
        filters.append(RiskAssessment.review_status == review_status)
    if search is not None:
        term = f"%{search.lower()}%"
        filters.append(or_(Transaction.tx_hash.like(term), Transaction.from_address.like(term), Transaction.to_address.like(term)))
    if min_score is not None and max_score is not None and min_score > max_score:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="min_score must be less than or equal to max_score")
    total = session.scalar(select(func.count()).select_from(query.where(*filters).subquery())) or 0
    rows = session.execute(
        query.where(*filters)
        .order_by(RiskAssessment.risk_score.desc(), RiskAssessment.assessed_at.desc(), RiskAssessment.id.desc())
        .limit(limit).offset(offset)
    ).all()
    items = [AssessmentRead.model_validate({**assessment.__dict__, "transaction": transaction}) for assessment, transaction in rows]
    return AlertPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/assessments/{assessment_id}", response_model=AssessmentRead)
def get_assessment(assessment_id: int, session: Annotated[Session, Depends(get_db)]) -> AssessmentRead:
    row = session.execute(
        select(RiskAssessment, Transaction)
        .join(Transaction, Transaction.id == RiskAssessment.transaction_id)
        .where(RiskAssessment.id == assessment_id)
    ).first()
    if row is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Assessment not found")
    assessment, transaction = row
    return AssessmentRead.model_validate({**assessment.__dict__, "transaction": transaction})
