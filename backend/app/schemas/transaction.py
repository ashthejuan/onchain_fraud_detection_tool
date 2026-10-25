from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def normalize_address(value: str | None) -> str | None:
    if value is None:
        return None
    address = value.strip()
    if not address:
        return None
    return address.lower() if address[:2].lower() == "0x" else address


def normalize_hash(value: str) -> str:
    tx_hash = value.strip()
    return tx_hash.lower() if tx_hash[:2].lower() == "0x" else tx_hash


class TransactionInput(BaseModel):
    chain_id: int = Field(gt=0)
    tx_hash: str = Field(min_length=1, max_length=256)
    from_address: str = Field(min_length=1, max_length=256)
    to_address: str | None = Field(default=None, max_length=256)
    amount: Decimal = Field(ge=0, max_digits=38, decimal_places=18)
    asset_symbol: str = Field(min_length=1, max_length=32)
    timestamp: datetime
    status: Literal["success", "failed", "pending"]
    block_number: int | None = Field(default=None, ge=0)

    @field_validator("tx_hash")
    @classmethod
    def clean_hash(cls, value: str) -> str:
        normalized = normalize_hash(value)
        if not normalized:
            raise ValueError("tx_hash is required")
        return normalized

    @field_validator("from_address")
    @classmethod
    def clean_sender(cls, value: str) -> str:
        normalized = normalize_address(value)
        if normalized is None:
            raise ValueError("from_address is required")
        return normalized

    @field_validator("to_address")
    @classmethod
    def clean_recipient(cls, value: str | None) -> str | None:
        return normalize_address(value)

    @field_validator("asset_symbol")
    @classmethod
    def clean_asset_symbol(cls, value: str) -> str:
        symbol = value.strip()
        if not symbol:
            raise ValueError("asset_symbol is required")
        return symbol.upper()

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, value: object) -> Decimal:
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, ValueError) as error:
            raise ValueError("amount must be a decimal number") from error
        if not amount.is_finite():
            raise ValueError("amount must be finite")
        return amount


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chain_id: int
    tx_hash: str
    from_address: str
    to_address: str | None
    amount: Decimal
    asset_symbol: str
    block_number: int | None
    block_timestamp: datetime
    status: Literal["success", "failed", "pending"]


class TransactionPage(BaseModel):
    items: list[TransactionRead]
    total: int
    limit: int
    offset: int
