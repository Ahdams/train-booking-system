from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from ..dependencies import DbSession, get_current_user, require_admin
from ..models import Booking, Report, User
from ..schemas.report import ReportCreate, ReportResolve, ReportResponse

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def to_response(report: Report) -> ReportResponse:
    return ReportResponse.model_validate(report, from_attributes=True)


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    payload: ReportCreate,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if payload.booking_id is not None:
        booking = db.get(Booking, payload.booking_id)
        if not booking or booking.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Booking not found")

    report = Report(
        user_id=current_user.id,
        booking_id=payload.booking_id,
        subject=payload.subject.strip(),
        description=payload.description.strip(),
        status="open",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return to_response(report)


@router.get("/mine", response_model=list[ReportResponse])
def my_reports(db: DbSession, current_user: Annotated[User, Depends(get_current_user)]):
    reports = db.scalars(
        select(Report).where(Report.user_id == current_user.id).order_by(Report.created_at.desc())
    ).all()
    return [to_response(report) for report in reports]


@router.get("", response_model=list[ReportResponse])
def admin_reports(
    db: DbSession,
    _: Annotated[User, Depends(require_admin)],
    report_status: str | None = None,
):
    stmt = select(Report).order_by(Report.created_at.desc())
    if report_status:
        stmt = stmt.where(Report.status == report_status)
    reports = db.scalars(stmt).all()
    return [to_response(report) for report in reports]


@router.patch("/{report_id}/resolve", response_model=ReportResponse)
def resolve_report(
    report_id: int,
    payload: ReportResolve,
    db: DbSession,
    _: Annotated[User, Depends(require_admin)],
):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = "resolved"
    report.admin_response = payload.admin_response.strip()
    report.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(report)
    return to_response(report)
