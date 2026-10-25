from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.transaction import TransactionRead


class AssessmentRead(BaseModel):
    id: int
    transaction_id: int
    risk_score: int
    severity: str
    triggered_rules: list[dict[str, Any]]
    ruleset_version: str
    assessed_at: datetime
    review_status: str
    transaction: TransactionRead


class AlertPage(BaseModel):
    items: list[AssessmentRead]
    total: int
    limit: int
    offset: int
