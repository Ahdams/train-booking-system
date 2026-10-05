from datetime import date, datetime
from decimal import Decimal
from secrets import token_hex
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from ..dependencies import DbSession, get_current_user, require_admin
from ..models import Booking, BookingStatusHistory, Schedule, Train, User
from ..schemas.booking import BookingCreate, BookingResponse, BookingStatusUpdate

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])

ALLOWED_STATUSES = {"confirmed", "completed", "cancelled"}


def make_reference() -> str:
    return f"TRN-{token_hex(5).upper()}"


def to_response(booking: Booking) -> BookingResponse:
    return BookingResponse.model_validate(booking, from_attributes=True)


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if payload.travel_date < date.today():
        raise HTTPException(status_code=400, detail="Travel date cannot be in the past")

    schedule = db.get(Schedule, payload.schedule_id)
    if not schedule or schedule.status != "active":
        raise HTTPException(status_code=404, detail="Schedule not found")

    train = db.get(Train, schedule.train_id)
    if not train or not train.is_active:
        raise HTTPException(status_code=404, detail="Train not found")

    if schedule.operating_days.split(",").count(payload.travel_date.strftime("%a")) == 0:
        raise HTTPException(status_code=400, detail="This train does not operate on the selected date")

    seat = payload.seat_number.strip().upper()
    booked = db.scalar(
        select(func.count(Booking.id)).where(
            Booking.schedule_id == schedule.id,
            Booking.travel_date == payload.travel_date,
            Booking.seat_number == seat,
            Booking.status == "confirmed",
        )
    ) or 0
    if booked:
        raise HTTPException(status_code=409, detail="That seat is already booked")

    booking = Booking(
        booking_reference=make_reference(),
        user_id=current_user.id,
        schedule_id=schedule.id,
        travel_date=payload.travel_date,
        seat_number=seat,
        amount=Decimal("0.00"),
        status="confirmed",
    )
    db.add(booking)
    db.flush()
    db.add(BookingStatusHistory(booking_id=booking.id, old_status=None, new_status="confirmed", changed_by_user_id=current_user.id, note="Booking created"))

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="That seat was booked by another passenger")

    db.refresh(booking)
    return to_response(booking)


@router.get("/mine", response_model=list[BookingResponse])
def my_bookings(db: DbSession, current_user: Annotated[User, Depends(get_current_user)]):
    bookings = db.scalars(select(Booking).where(Booking.user_id == current_user.id).order_by(Booking.created_at.desc())).all()
    return [to_response(b) for b in bookings]


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, db: DbSession, current_user: Annotated[User, Depends(get_current_user)]):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You cannot access this booking")
    return to_response(booking)


@router.patch("/{booking_id}/status", response_model=BookingResponse)
def update_booking_status(
    booking_id: int,
    payload: BookingStatusUpdate,
    db: DbSession,
    admin: Annotated[User, Depends(require_admin)],
):
    if payload.status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid booking status")
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status == payload.status:
        return booking

    old_status = booking.status
    booking.status = payload.status
    db.add(BookingStatusHistory(booking_id=booking.id, old_status=old_status, new_status=payload.status, changed_by_user_id=admin.id, note=payload.note))
    db.commit()
    db.refresh(booking)
    return booking
