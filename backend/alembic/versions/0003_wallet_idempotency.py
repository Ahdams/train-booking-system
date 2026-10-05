"""scope wallet idempotency keys per wallet

Revision ID: 0003_wallet_idempotency
Revises: 0002_align_booking_and_wallet_schema
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_wallet_idempotency"
down_revision = "0002_align_booking_and_wallet_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("wallet_transactions", sa.Column("idempotency_key", sa.String(80), nullable=True))
    # Existing development rows, if any, receive unique values before the column becomes required.
    op.execute("UPDATE wallet_transactions SET idempotency_key = reference WHERE idempotency_key IS NULL")
    op.alter_column("wallet_transactions", "idempotency_key", nullable=False)
    op.create_unique_constraint(
        "uq_wallet_transaction_idempotency",
        "wallet_transactions",
        ["wallet_id", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_wallet_transaction_idempotency", "wallet_transactions", type_="unique")
    op.drop_column("wallet_transactions", "idempotency_key")
