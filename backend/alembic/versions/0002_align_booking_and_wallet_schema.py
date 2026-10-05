"""align booking and wallet indexes with the initial schema

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
    # The initial schema already contains the current booking-status-history
    # columns and wallet fields. This migration only changes the seat index so
    # cancelled bookings release their seats.
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
