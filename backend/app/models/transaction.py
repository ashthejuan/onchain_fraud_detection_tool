from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("chain_id", "tx_hash", name="uq_transactions_chain_hash"),
        Index("ix_transactions_from_address", "from_address"),
        Index("ix_transactions_to_address", "to_address"),
        Index("ix_transactions_block_timestamp", "block_timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chain_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    tx_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    from_address: Mapped[str] = mapped_column(String(256), nullable=False)
    to_address: Mapped[str | None] = mapped_column(String(256), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    asset_symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    block_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    block_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
