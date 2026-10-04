from datetime import time

from sqlalchemy import ForeignKey, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    train_id: Mapped[int] = mapped_column(ForeignKey("trains.id"), nullable=False, index=True)
    origin_station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False)
    destination_station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False)
    departure_time: Mapped[time] = mapped_column(Time, nullable=False)
    arrival_time: Mapped[time] = mapped_column(Time, nullable=False)
    operating_days: Mapped[str] = mapped_column(String(80), nullable=False, default="Mon,Tue,Wed,Thu,Fri,Sat,Sun")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")

    train = relationship("Train")
    origin_station = relationship("Station", foreign_keys=[origin_station_id])
    destination_station = relationship("Station", foreign_keys=[destination_station_id])
