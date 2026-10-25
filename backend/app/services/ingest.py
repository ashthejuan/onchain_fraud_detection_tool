import csv
import io
from typing import Any

from pydantic import ValidationError
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Transaction, Wallet
from app.schemas.ingest import IngestSummary, RowError
from app.schemas.transaction import TransactionInput
from app.services.risk import persist_assessment

REQUIRED_COLUMNS = {
    "chain_id",
    "tx_hash",
    "from_address",
    "to_address",
    "amount",
    "asset_symbol",
    "timestamp",
    "status",
}
MAX_ERROR_SAMPLES = 100


def _format_validation_error(error: ValidationError) -> str:
    first_error = error.errors()[0]
    field = ".".join(str(part) for part in first_error["loc"])
    return f"{field}: {first_error['msg']}"


def _insert_wallet(session: Session, chain_id: int, address: str | None) -> None:
    if address is None:
        return
    statement = sqlite_insert(Wallet).values(
        chain_id=chain_id,
        address=address,
        is_flagged=False,
    )
    session.execute(statement.on_conflict_do_nothing(index_elements=["chain_id", "address"]))


def ingest_csv(session: Session, csv_bytes: bytes) -> IngestSummary:
    try:
        text = csv_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("CSV must be UTF-8 encoded") from error

    reader = csv.DictReader(io.StringIO(text, newline=""))
    headers = reader.fieldnames or []
    missing_columns = sorted(REQUIRED_COLUMNS.difference(headers))
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    if len(headers) != len(set(headers)):
        raise ValueError("CSV contains duplicate column names")

    accepted = 0
    rejected = 0
    duplicates = 0
    errors: list[RowError] = []
    assessment_ids: list[int] = []

    for row in reader:
        row_number = reader.line_num
        if None in row:
            rejected += 1
            if len(errors) < MAX_ERROR_SAMPLES:
                errors.append(RowError(row=row_number, error="row has more values than the header"))
            continue
        payload: dict[str, Any] = {key: value.strip() if value is not None else "" for key, value in row.items()}
        try:
            block_number = payload.get("block_number", "")
            payload["block_number"] = int(block_number) if block_number else None
            transaction = TransactionInput.model_validate(payload)
        except (ValidationError, ValueError, TypeError) as error:
            rejected += 1
            if len(errors) < MAX_ERROR_SAMPLES:
                message = _format_validation_error(error) if isinstance(error, ValidationError) else str(error)
                errors.append(RowError(row=row_number, error=message))
            continue

        statement = sqlite_insert(Transaction).values(
            chain_id=transaction.chain_id,
            tx_hash=transaction.tx_hash,
            from_address=transaction.from_address,
            to_address=transaction.to_address,
            amount=transaction.amount,
            asset_symbol=transaction.asset_symbol,
            block_number=transaction.block_number,
            block_timestamp=transaction.timestamp,
            status=transaction.status,
        )
        result = session.execute(
            statement.on_conflict_do_nothing(index_elements=["chain_id", "tx_hash"])
        )
        if result.rowcount == 0:
            duplicates += 1
            continue

        accepted += 1
        _insert_wallet(session, transaction.chain_id, transaction.from_address)
        _insert_wallet(session, transaction.chain_id, transaction.to_address)
        stored_transaction = session.scalar(
            select(Transaction).where(
                Transaction.chain_id == transaction.chain_id,
                Transaction.tx_hash == transaction.tx_hash,
            )
        )
        if stored_transaction is None:
            raise RuntimeError("Inserted transaction could not be retrieved")
        assessment_ids.append(stored_transaction.id)

    if assessment_ids:
        transactions = session.scalars(
            select(Transaction)
            .where(Transaction.id.in_(assessment_ids))
            .order_by(Transaction.block_timestamp, Transaction.id)
        ).all()
        for transaction in transactions:
            persist_assessment(session, transaction)

    session.commit()
    return IngestSummary(
        accepted=accepted,
        rejected=rejected,
        duplicates=duplicates,
        errors=errors,
        errors_truncated=rejected > len(errors),
    )
