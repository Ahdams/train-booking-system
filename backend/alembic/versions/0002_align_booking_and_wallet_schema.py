"""align booking status history and wallet schema

Revision ID: 0002_align_booking_and_wallet_schema
Revises: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_align_booking_and_wallet_schema"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Align the database with the BookingStatusHistory ORM model.
    op.add_column("booking_status_history", sa.Column("old_status", sa.String(30), nullable=True))
    op.alter_column("booking_status_history", "status", new_column_name="new_status")

    # 0001 already creates wallet_transactions.booking_id and its index.
    # No duplicate column/index should be created here.

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
    op.alter_column("booking_status_history", "new_status", new_column_name="status")
    op.drop_column("booking_status_history", "old_status")
