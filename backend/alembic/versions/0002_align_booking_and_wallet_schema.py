"""align booking status history and wallet relationships

Revision ID: 0002_align_booking_and_wallet_schema
Revises: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_align_booking_and_wallet_schema"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Align the database with the BookingStatusHistory ORM model.
    op.add_column("booking_status_history", sa.Column("old_status", sa.String(30), nullable=True))
    op.alter_column("booking_status_history", "status", new_column_name="new_status")

    # Link wallet transactions to the booking that caused the transaction.
    op.add_column("wallet_transactions", sa.Column("booking_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_wallet_transactions_booking_id",
        "wallet_transactions",
        "bookings",
        ["booking_id"],
        ["id"],
    )
    op.create_index("ix_wallet_transactions_booking_id", "wallet_transactions", ["booking_id"])

    # A cancelled booking must release its seat so it can be booked again.
    op.drop_index("uq_booking_seat_per_service_date", table_name="bookings")
    op.create_index(
        "uq_active_booking_seat_per_service_date",
        "bookings",
        ["schedule_id", "travel_date", "seat_number"],
        unique=True,
        postgresql_where=sa.text("status IN ('confirmed', 'completed')"),
    )


def downgrade() -> None:
    op.drop_index("uq_active_booking_seat_per_service_date", table_name="bookings")
    op.create_index(
        "uq_booking_seat_per_service_date",
        "bookings",
        ["schedule_id", "travel_date", "seat_number"],
        unique=True,
    )
    op.drop_index("ix_wallet_transactions_booking_id", table_name="wallet_transactions")
    op.drop_constraint("fk_wallet_transactions_booking_id", "wallet_transactions", type_="foreignkey")
    op.drop_column("wallet_transactions", "booking_id")
    op.alter_column("booking_status_history", "new_status", new_column_name="status")
    op.drop_column("booking_status_history", "old_status")
