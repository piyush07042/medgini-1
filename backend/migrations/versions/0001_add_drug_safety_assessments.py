"""Add drug_safety_assessments table

Revision ID: 0001_add_drug_safety_assessments
Revises: None
Create Date: 2026-08-05 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_add_drug_safety_assessments"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "drug_safety_assessments",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=True),
        sa.Column("medications", sa.JSON(), nullable=False),
        sa.Column("allergies", sa.JSON(), nullable=True),
        sa.Column("assessment", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("drug_safety_assessments")
