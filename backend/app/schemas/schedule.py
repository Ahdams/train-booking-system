from datetime import date, time

from pydantic import BaseModel, Field, field_validator


VALID_DAYS = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}


class ScheduleCreate(BaseModel):
    train_id: int
    origin_station_id: int
    destination_station_id: int
    departure_time: time
    arrival_time: time
    operating_days: list[str] = Field(min_length=1)
    status: str = "active"

    @field_validator("operating_days")
    @classmethod
    def validate_days(cls, value: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(day[:3].title() for day in value))
        if any(day not in VALID_DAYS for day in normalized):
            raise ValueError("operating_days must contain Mon, Tue, Wed, Thu, Fri, Sat, or Sun")
        return normalized


class ScheduleResponse(BaseModel):
    id: int
    train_id: int
    origin_station_id: int
    destination_station_id: int
    departure_time: time
    arrival_time: time
    operating_days: list[str]
    status: str


class TrainCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    train_number: str = Field(min_length=1, max_length=50)
    total_seats: int = Field(default=100, ge=1, le=5000)


class TrainResponse(BaseModel):
    id: int
    name: str
    train_number: str
    total_seats: int
    is_active: bool


class StationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    code: str = Field(min_length=2, max_length=20)


class StationResponse(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool


class TrainSearchResponse(BaseModel):
    schedule_id: int
    train_id: int
    train_name: str
    train_number: str
    origin_station_id: int
    origin_station: str
    destination_station_id: int
    destination_station: str
    departure_time: time
    arrival_time: time
    operating_days: list[str]
    available_seats: int
    travel_date: date | None = None
