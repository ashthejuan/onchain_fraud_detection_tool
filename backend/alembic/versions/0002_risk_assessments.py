"""Add append-only risk assessments.

Revision ID: 0002_risk_assessments
Revises: 0001_foundation
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_risk_assessments"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("triggered_rules", sa.JSON(), nullable=False),
        sa.Column("ruleset_version", sa.String(length=32), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("review_status", sa.String(length=16), nullable=False, server_default="open"),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assessments_transaction_id", "risk_assessments", ["transaction_id"])
    op.create_index("ix_assessments_severity", "risk_assessments", ["severity"])
    op.create_index("ix_assessments_risk_score", "risk_assessments", ["risk_score"])
    op.create_index("ix_assessments_assessed_at", "risk_assessments", ["assessed_at"])


def downgrade() -> None:
    op.drop_index("ix_assessments_assessed_at", table_name="risk_assessments")
    op.drop_index("ix_assessments_risk_score", table_name="risk_assessments")
    op.drop_index("ix_assessments_severity", table_name="risk_assessments")
    op.drop_index("ix_assessments_transaction_id", table_name="risk_assessments")
    op.drop_table("risk_assessments")
