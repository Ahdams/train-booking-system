from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("schedule_id", "travel_date", "seat_number", name="uq_booking_schedule_date_seat"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_reference: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id"), nullable=False)
    travel_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    seat_number: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="confirmed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")
    schedule = relationship("Schedule")
