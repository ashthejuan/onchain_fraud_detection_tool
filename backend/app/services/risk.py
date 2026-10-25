from sqlalchemy.orm import Session

from app.models import RiskAssessment, Transaction
from app.rules.v1 import assess_transaction


def persist_assessment(session: Session, transaction: Transaction) -> RiskAssessment:
    return assess_transaction(session, transaction)
