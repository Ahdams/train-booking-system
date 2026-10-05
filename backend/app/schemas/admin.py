from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class AdminDashboardResponse(BaseModel):
    total_users: int
    active_users: int
    total_trains: int
    active_trains: int
    total_schedules: int
    active_schedules: int
    total_bookings: int
    confirmed_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    open_reports: int
    resolved_reports: int
    wallet_credit_volume: Decimal
    wallet_debit_volume: Decimal
    bookings_today: int
    dashboard_date: date
