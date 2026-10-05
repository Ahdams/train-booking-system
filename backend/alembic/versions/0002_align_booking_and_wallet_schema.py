"""align booking seat index with the initial schema

Revision ID: 0002_wallet_seat_index
Revises: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_wallet_seat_index"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cancelled bookings must release their seats for future bookings.
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
