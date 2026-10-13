"""Add admin-configured schedule fares. Existing schedules require fare setup.

Revision ID: 0004_schedule_fares
Revises: 0003_wallet_idempotency
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_schedule_fares"
down_revision = "0003_wallet_idempotency"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("schedules", sa.Column("fare", sa.Numeric(12, 2), nullable=True))

def downgrade():
    op.drop_column("schedules", "fare")
