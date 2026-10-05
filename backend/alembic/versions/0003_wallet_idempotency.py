"""finalize wallet idempotency schema

Revision ID: 0003_wallet_idempotency
Revises: 0002_align_booking_and_wallet_schema
"""

revision = "0003_wallet_idempotency"
down_revision = "0002_align_booking_and_wallet_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The initial schema already contains idempotency_key and its
    # wallet-scoped unique index. This revision is intentionally a no-op.
    pass


def downgrade() -> None:
    # Keep the schema from 0002; the idempotency fields are part of the
    # initial schema and therefore are not removed here.
    pass
