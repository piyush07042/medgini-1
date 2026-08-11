"""Add patient avatar_url column

Revision ID: 0002_add_patient_avatar_url
Revises: 0001_add_drug_safety_assessments
Create Date: 2026-08-07 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_patient_avatar_url"
down_revision = "0001_add_drug_safety_assessments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("patients", sa.Column("avatar_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("patients", "avatar_url")
