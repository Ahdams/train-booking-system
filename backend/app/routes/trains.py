from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import DbSession, require_admin
from ..models import Booking, Schedule, Station, Train, User
from ..schemas.schedule import (
    ScheduleCreate,
    ScheduleResponse,
    StationCreate,
    StationResponse,
    TrainCreate,
    TrainResponse,
    TrainSearchResponse,
)

router = APIRouter(prefix="/api", tags=["Trains & Schedules"])


@router.get("/stations", response_model=list[StationResponse])
def list_stations(db: DbSession):
    return db.scalars(select(Station).where(Station.is_active.is_(True)).order_by(Station.name)).all()


@router.post("/stations", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
def create_station(payload: StationCreate, db: DbSession, _: Annotated[User, Depends(require_admin)]):
    existing = db.scalar(select(Station).where((Station.name == payload.name) | (Station.code == payload.code.upper())))
    if existing:
        raise HTTPException(status_code=409, detail="Station name or code already exists")
    station = Station(name=payload.name.strip(), code=payload.code.upper())
    db.add(station)
    db.commit()
    db.refresh(station)
    return station


@router.get("/trains", response_model=list[TrainResponse])
def list_trains(db: DbSession):
    return db.scalars(select(Train).where(Train.is_active.is_(True)).order_by(Train.train_number)).all()


@router.post("/trains", response_model=TrainResponse, status_code=status.HTTP_201_CREATED)
def create_train(payload: TrainCreate, db: DbSession, _: Annotated[User, Depends(require_admin)]):
    existing = db.scalar(select(Train).where(Train.train_number == payload.train_number))
    if existing:
        raise HTTPException(status_code=409, detail="Train number already exists")
    train = Train(**payload.model_dump())
    db.add(train)
    db.commit()
    db.refresh(train)
    return train


def serialize_schedule(schedule: Schedule) -> ScheduleResponse:
    return ScheduleResponse(
        id=schedule.id,
        train_id=schedule.train_id,
        origin_station_id=schedule.origin_station_id,
        destination_station_id=schedule.destination_station_id,
        departure_time=schedule.departure_time,
        arrival_time=schedule.arrival_time,
        operating_days=[d for d in schedule.operating_days.split(",") if d],
        status=schedule.status,
    )


@router.post("/schedules", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(payload: ScheduleCreate, db: DbSession, _: Annotated[User, Depends(require_admin)]):
    train = db.get(Train, payload.train_id)
    origin = db.get(Station, payload.origin_station_id)
    destination = db.get(Station, payload.destination_station_id)
    if not train or not train.is_active:
        raise HTTPException(status_code=404, detail="Train not found")
    if not origin or not destination or not origin.is_active or not destination.is_active:
        raise HTTPException(status_code=404, detail="Station not found")
    if origin.id == destination.id:
        raise HTTPException(status_code=400, detail="Origin and destination must be different")
    if payload.arrival_time <= payload.departure_time:
        raise HTTPException(status_code=400, detail="Arrival time must be later than departure time")

    schedule = Schedule(
        train_id=payload.train_id,
        origin_station_id=payload.origin_station_id,
        destination_station_id=payload.destination_station_id,
        departure_time=payload.departure_time,
        arrival_time=payload.arrival_time,
        operating_days=",".join(payload.operating_days),
        status=payload.status,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return serialize_schedule(schedule)


@router.get("/schedules", response_model=list[ScheduleResponse])
def list_schedules(db: DbSession):
    schedules = db.scalars(select(Schedule).where(Schedule.status == "active").order_by(Schedule.departure_time)).all()
    return [serialize_schedule(schedule) for schedule in schedules]


@router.get("/trains/search", response_model=list[TrainSearchResponse])
def search_trains(
    db: DbSession,
    origin_station_id: int = Query(...),
    destination_station_id: int = Query(...),
    travel_date: date | None = Query(default=None),
    preferred_time: str | None = Query(default=None),
):
    if origin_station_id == destination_station_id:
        raise HTTPException(status_code=400, detail="Origin and destination must be different")

    stmt = (
        select(Schedule, Train, Station, Station)
        .join(Train, Schedule.train_id == Train.id)
        .join(Station, Schedule.origin_station_id == Station.id)
        .join(Station, Schedule.destination_station_id == Station.id)
        .where(
            Schedule.origin_station_id == origin_station_id,
            Schedule.destination_station_id == destination_station_id,
            Schedule.status == "active",
            Train.is_active.is_(True),
        )
    )

    # The explicit joins above use the Station table twice; use aliases for clarity.
    from sqlalchemy.orm import aliased
    origin = aliased(Station)
    destination = aliased(Station)
    stmt = (
        select(Schedule, Train, origin, destination)
        .join(Train, Schedule.train_id == Train.id)
        .join(origin, Schedule.origin_station_id == origin.id)
        .join(destination, Schedule.destination_station_id == destination.id)
        .where(
            Schedule.origin_station_id == origin_station_id,
            Schedule.destination_station_id == destination_station_id,
            Schedule.status == "active",
            Train.is_active.is_(True),
        )
        .order_by(Schedule.departure_time)
    )

    if travel_date:
        day = travel_date.strftime("%a")
        stmt = stmt.where(Schedule.operating_days.like(f"%{day}%"))

    rows = db.execute(stmt).all()
    results = []
    for schedule, train, origin_station, destination_station in rows:
        available = train.total_seats
        if travel_date:
            booked = db.scalar(
                select(Booking.id)
                .where(
                    Booking.schedule_id == schedule.id,
                    Booking.travel_date == travel_date,
                    Booking.status.in_(["confirmed", "completed"]),
                )
                .count()
            ) if False else None
            from sqlalchemy import func
            booked = db.scalar(
                select(func.count(Booking.id)).where(
                    Booking.schedule_id == schedule.id,
                    Booking.travel_date == travel_date,
                    Booking.status == "confirmed",
                )
            ) or 0
            available = max(0, train.total_seats - booked)

        results.append(
            TrainSearchResponse(
                schedule_id=schedule.id,
                train_id=train.id,
                train_name=train.name,
                train_number=train.train_number,
                origin_station_id=origin_station.id,
                origin_station=origin_station.name,
                destination_station_id=destination_station.id,
                destination_station=destination_station.name,
                departure_time=schedule.departure_time,
                arrival_time=schedule.arrival_time,
                operating_days=[d for d in schedule.operating_days.split(",") if d],
                available_seats=available,
                travel_date=travel_date,
            )
        )
    return results
