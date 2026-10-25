from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Transaction
from app.schemas.ingest import IngestSummary
from app.schemas.transaction import TransactionPage, TransactionRead, normalize_address, normalize_hash
from app.services.ingest import ingest_csv

router = APIRouter(prefix="/transactions", tags=["transactions"])
MAX_CSV_BYTES = 10 * 1024 * 1024


@router.post("/ingest", response_model=IngestSummary)
async def ingest_transactions(
    file: Annotated[UploadFile, File()],
    session: Annotated[Session, Depends(get_db)],
) -> IngestSummary:
    try:
        csv_bytes = await file.read(MAX_CSV_BYTES + 1)
    finally:
        await file.close()
    if len(csv_bytes) > MAX_CSV_BYTES:
        raise HTTPException(status_code=413, detail="CSV file exceeds the 10 MiB limit")
    try:
        return ingest_csv(session, csv_bytes)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("", response_model=TransactionPage)
def list_transactions(
    session: Annotated[Session, Depends(get_db)],
    chain_id: Annotated[int | None, Query(gt=0)] = None,
    address: Annotated[str | None, Query(min_length=1, max_length=256)] = None,
    status: Literal["success", "failed", "pending"] | None = None,
    from_timestamp: datetime | None = None,
    to_timestamp: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TransactionPage:
    if from_timestamp is not None and to_timestamp is not None and from_timestamp > to_timestamp:
        raise HTTPException(status_code=422, detail="from_timestamp must be before to_timestamp")

    filters = []
    if chain_id is not None:
        filters.append(Transaction.chain_id == chain_id)
    normalized_address = normalize_address(address)
    if normalized_address is not None:
        filters.append(
            or_(Transaction.from_address == normalized_address, Transaction.to_address == normalized_address)
        )
    if status is not None:
        filters.append(Transaction.status == status)
    if from_timestamp is not None:
        filters.append(Transaction.block_timestamp >= from_timestamp)
    if to_timestamp is not None:
        filters.append(Transaction.block_timestamp <= to_timestamp)

    total = session.scalar(select(func.count()).select_from(Transaction).where(*filters)) or 0
    rows = session.scalars(
        select(Transaction)
        .where(*filters)
        .order_by(Transaction.block_timestamp.desc(), Transaction.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return TransactionPage(items=rows, total=total, limit=limit, offset=offset)


@router.get("/{tx_hash}", response_model=TransactionRead)
def get_transaction(
    tx_hash: str,
    session: Annotated[Session, Depends(get_db)],
    chain_id: Annotated[int | None, Query(gt=0)] = None,
) -> Transaction:
    query = select(Transaction).where(Transaction.tx_hash == normalize_hash(tx_hash))
    if chain_id is not None:
        query = query.where(Transaction.chain_id == chain_id)
    rows = session.scalars(query.limit(2)).all()
    if not rows:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if len(rows) > 1:
        raise HTTPException(status_code=409, detail="Transaction hash exists on multiple chains; provide chain_id")
    return rows[0]
