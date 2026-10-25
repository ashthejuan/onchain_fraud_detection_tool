from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RiskAssessment, Transaction, Wallet

RULESET_VERSION = "ruleset-v1"
LARGE_TRANSFER_THRESHOLD = Decimal("100")
VELOCITY_COUNT = 5
VELOCITY_MINUTES = 10
RAPID_FUND_MINUTES = 30
FAILURE_COUNT = 3
FAILURE_MINUTES = 10
WEIGHTS = {
    "large_transfer": 25,
    "high_velocity": 25,
    "rapid_fund_movement": 30,
    "flagged_wallet_exposure": 40,
    "repeated_failures": 15,
}


@dataclass(frozen=True)
class RuleTrigger:
    rule_id: str
    weight: int
    observation: str
    evidence_refs: list[str]

    def as_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "weight": self.weight,
            "observation": self.observation,
            "evidence_refs": self.evidence_refs,
        }


def _severity(score: int) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _evidence(rule_id: str, transaction_ids: list[int]) -> list[str]:
    return [*(f"tx:{transaction_id}" for transaction_id in transaction_ids), f"cfg:{rule_id}"]


def assess_transaction(session: Session, transaction: Transaction) -> RiskAssessment:
    triggers: list[RuleTrigger] = []
    if transaction.amount >= LARGE_TRANSFER_THRESHOLD:
        triggers.append(RuleTrigger(
            "large_transfer", WEIGHTS["large_transfer"],
            f"Amount {transaction.amount} meets threshold {LARGE_TRANSFER_THRESHOLD}",
            _evidence("large_transfer_threshold", [transaction.id]),
        ))

    lower_bound = transaction.block_timestamp.replace(tzinfo=None)
    if transaction.status == "success":
        lower_bound -= timedelta(minutes=VELOCITY_MINUTES)
        velocity_ids = session.scalars(select(Transaction.id).where(
            Transaction.chain_id == transaction.chain_id,
            Transaction.from_address == transaction.from_address,
            Transaction.status == "success",
            Transaction.block_timestamp <= transaction.block_timestamp,
            Transaction.block_timestamp >= lower_bound,
        ).order_by(Transaction.block_timestamp.desc(), Transaction.id.desc()).limit(VELOCITY_COUNT)).all()
        if len(velocity_ids) >= VELOCITY_COUNT:
            triggers.append(RuleTrigger(
                "high_velocity", WEIGHTS["high_velocity"],
                f"At least {VELOCITY_COUNT} outgoing transfers in the prior {VELOCITY_MINUTES} minutes",
                _evidence("high_velocity_window", velocity_ids),
            ))

        inbound_start = transaction.block_timestamp.replace(tzinfo=None) - timedelta(minutes=RAPID_FUND_MINUTES)
        received_id = session.scalar(select(Transaction.id).where(
            Transaction.chain_id == transaction.chain_id,
            Transaction.to_address == transaction.from_address,
            Transaction.status == "success",
            Transaction.block_timestamp < transaction.block_timestamp,
            Transaction.block_timestamp >= inbound_start,
        ).order_by(Transaction.block_timestamp.desc(), Transaction.id.desc()).limit(1))
        if received_id is not None:
            triggers.append(RuleTrigger(
                "rapid_fund_movement", WEIGHTS["rapid_fund_movement"],
                f"Wallet sent funds after receiving a transfer within {RAPID_FUND_MINUTES} minutes",
                _evidence("rapid_fund_window", [received_id, transaction.id]),
            ))

    flagged_address = session.scalar(select(Wallet.address).where(
        Wallet.chain_id == transaction.chain_id,
        Wallet.is_flagged.is_(True),
        Wallet.address.in_([transaction.from_address, transaction.to_address or ""]),
    ).limit(1))
    if flagged_address is not None:
        triggers.append(RuleTrigger(
            "flagged_wallet_exposure", WEIGHTS["flagged_wallet_exposure"],
            "Sender or recipient is on the local flagged wallet list",
            [f"tx:{transaction.id}", "wallets:flagged"],
        ))

    if transaction.status == "failed":
        failures_start = transaction.block_timestamp.replace(tzinfo=None) - timedelta(minutes=FAILURE_MINUTES)
        failure_ids = session.scalars(select(Transaction.id).where(
            Transaction.chain_id == transaction.chain_id,
            Transaction.from_address == transaction.from_address,
            Transaction.status == "failed",
            Transaction.block_timestamp <= transaction.block_timestamp,
            Transaction.block_timestamp >= failures_start,
        ).order_by(Transaction.block_timestamp.desc(), Transaction.id.desc()).limit(FAILURE_COUNT)).all()
        if len(failure_ids) >= FAILURE_COUNT:
            triggers.append(RuleTrigger(
                "repeated_failures", WEIGHTS["repeated_failures"],
                f"At least {FAILURE_COUNT} failed transfers in the prior {FAILURE_MINUTES} minutes",
                _evidence("repeated_failures_window", failure_ids),
            ))

    # All triggered weights are summed; only the final score is capped at 100.
    score = min(100, sum(trigger.weight for trigger in triggers))
    assessment = RiskAssessment(
        transaction_id=transaction.id,
        risk_score=score,
        severity=_severity(score),
        triggered_rules=[trigger.as_dict() for trigger in triggers],
        ruleset_version=RULESET_VERSION,
    )
    session.add(assessment)
    session.flush()
    return assessment
