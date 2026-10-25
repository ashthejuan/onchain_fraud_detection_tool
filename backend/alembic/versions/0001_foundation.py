"""Create transaction and wallet tables.

Revision ID: 0001_foundation
Revises:
Create Date: 2026-10-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("tx_hash", sa.String(length=256), nullable=False),
        sa.Column("from_address", sa.String(length=256), nullable=False),
        sa.Column("to_address", sa.String(length=256), nullable=True),
        sa.Column("amount", sa.Numeric(precision=38, scale=18), nullable=False),
        sa.Column("asset_symbol", sa.String(length=32), nullable=False),
        sa.Column("block_number", sa.Integer(), nullable=True),
        sa.Column("block_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chain_id", "tx_hash", name="uq_transactions_chain_hash"),
    )
    op.create_index("ix_transactions_chain_id", "transactions", ["chain_id"])
    op.create_index("ix_transactions_from_address", "transactions", ["from_address"])
    op.create_index("ix_transactions_to_address", "transactions", ["to_address"])
    op.create_index("ix_transactions_block_timestamp", "transactions", ["block_timestamp"])

    op.create_table(
        "wallets",
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(length=256), nullable=False),
        sa.Column("is_flagged", sa.Boolean(), nullable=False),
        sa.Column("flag_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("chain_id", "address"),
    )


def downgrade() -> None:
    op.drop_table("wallets")
    op.drop_index("ix_transactions_block_timestamp", table_name="transactions")
    op.drop_index("ix_transactions_to_address", table_name="transactions")
    op.drop_index("ix_transactions_from_address", table_name="transactions")
    op.drop_index("ix_transactions_chain_id", table_name="transactions")
    op.drop_table("transactions")
