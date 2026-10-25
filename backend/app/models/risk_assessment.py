from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    __table_args__ = (
        Index("ix_assessments_transaction_id", "transaction_id"),
        Index("ix_assessments_severity", "severity"),
        Index("ix_assessments_risk_score", "risk_score"),
        Index("ix_assessments_assessed_at", "assessed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    triggered_rules: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    ruleset_version: Mapped[str] = mapped_column(String(32), nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    review_status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
