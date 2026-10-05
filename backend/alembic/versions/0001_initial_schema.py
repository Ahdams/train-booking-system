"""create initial train booking schema

Revision ID: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("full_name", sa.String(150), nullable=False), sa.Column("email", sa.String(255), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("phone", sa.String(30)), sa.Column("nin", sa.String(30)), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("stations", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("code", sa.String(20), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index("ix_stations_name", "stations", ["name"], unique=True)
    op.create_index("ix_stations_code", "stations", ["code"], unique=True)
    op.create_table("trains", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("train_number", sa.String(50), nullable=False), sa.Column("total_seats", sa.Integer(), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index("ix_trains_train_number", "trains", ["train_number"], unique=True)
    op.create_table("schedules", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("train_id", sa.Integer(), sa.ForeignKey("trains.id"), nullable=False), sa.Column("origin_station_id", sa.Integer(), sa.ForeignKey("stations.id"), nullable=False), sa.Column("destination_station_id", sa.Integer(), sa.ForeignKey("stations.id"), nullable=False), sa.Column("departure_time", sa.Time(), nullable=False), sa.Column("arrival_time", sa.Time(), nullable=False), sa.Column("operating_days", sa.String(80), nullable=False), sa.Column("status", sa.String(30), nullable=False, server_default="active"))
    op.create_index("ix_schedules_train_id", "schedules", ["train_id"])
    op.create_index("uq_schedule_route_time", "schedules", ["train_id", "origin_station_id", "destination_station_id", "departure_time"], unique=True)
    op.create_table("bookings", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("booking_reference", sa.String(30), nullable=False), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("schedule_id", sa.Integer(), sa.ForeignKey("schedules.id"), nullable=False), sa.Column("travel_date", sa.Date(), nullable=False), sa.Column("seat_number", sa.String(20), nullable=False), sa.Column("amount", sa.Numeric(12, 2), nullable=False), sa.Column("status", sa.String(30), nullable=False, server_default="confirmed"), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_bookings_booking_reference", "bookings", ["booking_reference"], unique=True)
    op.create_index("ix_bookings_user_id", "bookings", ["user_id"])
    op.create_index("ix_bookings_travel_date", "bookings", ["travel_date"])
    op.create_index("uq_booking_seat_per_service_date", "bookings", ["schedule_id", "travel_date", "seat_number"], unique=True, postgresql_where=sa.text("status IN ('confirmed', 'completed')"))
    op.create_table("booking_status_history", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False), sa.Column("old_status", sa.String(30)), sa.Column("new_status", sa.String(30), nullable=False), sa.Column("changed_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True), sa.Column("note", sa.Text()), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_booking_status_history_booking_id", "booking_status_history", ["booking_id"])
    op.create_table("wallets", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("balance", sa.Numeric(12, 2), nullable=False, server_default="0"), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_wallets_user_id", "wallets", ["user_id"], unique=True)
    op.create_table("wallet_transactions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("wallet_id", sa.Integer(), sa.ForeignKey("wallets.id"), nullable=False), sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id"), nullable=True), sa.Column("transaction_type", sa.String(30), nullable=False), sa.Column("amount", sa.Numeric(12, 2), nullable=False), sa.Column("reference", sa.String(80), nullable=False), sa.Column("idempotency_key", sa.String(80), nullable=False), sa.Column("description", sa.String(255), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_wallet_transactions_wallet_id", "wallet_transactions", ["wallet_id"])
    op.create_index("ix_wallet_transactions_reference", "wallet_transactions", ["reference"], unique=True)
    op.create_index("ix_wallet_transactions_booking_id", "wallet_transactions", ["booking_id"])
    op.create_index("uq_wallet_transaction_idempotency", "wallet_transactions", ["wallet_id", "idempotency_key"], unique=True)
    op.create_table("reports", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id"), nullable=True), sa.Column("subject", sa.String(150), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("status", sa.String(30), nullable=False, server_default="open"), sa.Column("admin_response", sa.Text()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("resolved_at", sa.DateTime()))
    op.create_index("ix_reports_user_id", "reports", ["user_id"])
    op.create_index("ix_reports_booking_id", "reports", ["booking_id"])


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("wallet_transactions")
    op.drop_table("wallets")
    op.drop_table("booking_status_history")
    op.drop_table("bookings")
    op.drop_table("schedules")
    op.drop_table("trains")
    op.drop_table("stations")
    op.drop_table("users")
