from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Wallet
from app.schemas.transaction import normalize_address

router = APIRouter(prefix="/wallets", tags=["wallets"])


class WalletRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chain_id: int
    address: str
    is_flagged: bool
    flag_reason: str | None
    created_at: datetime


@router.get("/{address}", response_model=WalletRead | None)
def get_wallet(
    address: str,
    session: Annotated[Session, Depends(get_db)],
    chain_id: Annotated[int, Query(gt=0)],
) -> Wallet | None:
    normalized_address = normalize_address(address)
    if normalized_address is None:
        raise HTTPException(status_code=422, detail="address is required")
    return session.scalar(
        select(Wallet).where(Wallet.chain_id == chain_id, Wallet.address == normalized_address)
    )
