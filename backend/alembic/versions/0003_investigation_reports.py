"""Add persisted LLM investigation reports."""
from alembic import op
import sqlalchemy as sa

revision = "0003_investigation_reports"
down_revision = "0002_risk_assessments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "investigation_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("evidence_snapshot", sa.JSON(), nullable=False),
        sa.Column("report_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assessment_id"], ["risk_assessments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investigation_reports_assessment_id", "investigation_reports", ["assessment_id"])


def downgrade() -> None:
    op.drop_index("ix_investigation_reports_assessment_id", table_name="investigation_reports")
    op.drop_table("investigation_reports")
