from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from ..dependencies import DbSession, require_admin
from ..models import Booking, Report, Schedule, Train, User, WalletTransaction
from ..schemas.admin import AdminDashboardResponse

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/dashboard", response_model=AdminDashboardResponse)
def dashboard(
    db: DbSession,
    _: Annotated[User, Depends(require_admin)],
):
    today = date.today()

    total_users = db.scalar(select(func.count(User.id))) or 0
    active_users = db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0
    total_trains = db.scalar(select(func.count(Train.id))) or 0
    active_trains = db.scalar(select(func.count(Train.id)).where(Train.is_active.is_(True))) or 0
    total_schedules = db.scalar(select(func.count(Schedule.id))) or 0
    active_schedules = db.scalar(select(func.count(Schedule.id)).where(Schedule.status == "active")) or 0
    total_bookings = db.scalar(select(func.count(Booking.id))) or 0
    confirmed = db.scalar(select(func.count(Booking.id)).where(Booking.status == "confirmed")) or 0
    completed = db.scalar(select(func.count(Booking.id)).where(Booking.status == "completed")) or 0
    cancelled = db.scalar(select(func.count(Booking.id)).where(Booking.status == "cancelled")) or 0
    open_reports = db.scalar(select(func.count(Report.id)).where(Report.status == "open")) or 0
    resolved_reports = db.scalar(select(func.count(Report.id)).where(Report.status == "resolved")) or 0
    bookings_today = db.scalar(select(func.count(Booking.id)).where(Booking.travel_date == today)) or 0

    credit_volume = db.scalar(
        select(func.coalesce(func.sum(WalletTransaction.amount), 0)).where(
            WalletTransaction.transaction_type == "credit"
        )
    ) or Decimal("0.00")
    debit_volume = db.scalar(
        select(func.coalesce(func.sum(WalletTransaction.amount), 0)).where(
            WalletTransaction.transaction_type == "debit"
        )
    ) or Decimal("0.00")

    return AdminDashboardResponse(
        total_users=total_users,
        active_users=active_users,
        total_trains=total_trains,
        active_trains=active_trains,
        total_schedules=total_schedules,
        active_schedules=active_schedules,
        total_bookings=total_bookings,
        confirmed_bookings=confirmed,
        completed_bookings=completed,
        cancelled_bookings=cancelled,
        open_reports=open_reports,
        resolved_reports=resolved_reports,
        wallet_credit_volume=credit_volume,
        wallet_debit_volume=debit_volume,
        bookings_today=bookings_today,
        dashboard_date=today,
    )
