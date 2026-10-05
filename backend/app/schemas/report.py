from datetime import datetime

from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=5, max_length=2000)
    booking_id: int | None = None


class ReportResponse(BaseModel):
    id: int
    user_id: int
    booking_id: int | None
    subject: str
    description: str
    status: str
    admin_response: str | None
    created_at: datetime
    resolved_at: datetime | None


class ReportResolve(BaseModel):
    admin_response: str = Field(min_length=2, max_length=2000)
