from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class BookingCreate(BaseModel):
    schedule_id: int
    travel_date: date
    seat_number: str = Field(min_length=1, max_length=20)


class BookingResponse(BaseModel):
    id: int
    booking_reference: str
    schedule_id: int
    travel_date: date
    seat_number: str
    amount: Decimal
    status: str
    created_at: datetime


class BookingStatusUpdate(BaseModel):
    status: str
    note: str | None = Field(default=None, max_length=500)
