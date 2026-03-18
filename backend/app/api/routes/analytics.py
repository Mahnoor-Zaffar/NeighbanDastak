from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps.permissions import QueueActor, get_queue_actor
from app.db.session import get_db_session
from app.schemas.analytics import (
    AppointmentStatusBreakdownResponse,
    AnalyticsSummaryResponse,
    AppointmentsByDayResponse,
    DoctorWorkloadResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["analytics"])

AnalyticsActor = Annotated[QueueActor, Depends(get_queue_actor)]


def get_analytics_service(session: Annotated[Session, Depends(get_db_session)]) -> AnalyticsService:
    return AnalyticsService(session)


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
@router.get("/metrics/summary", response_model=AnalyticsSummaryResponse)
@router.get("/insights/summary", response_model=AnalyticsSummaryResponse)
def get_summary(
    actor: AnalyticsActor,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    doctor_id: UUID | None = None,
) -> AnalyticsSummaryResponse:
    return service.get_summary(actor=actor, doctor_id=doctor_id)


@router.get("/analytics/appointments-by-day", response_model=AppointmentsByDayResponse)
@router.get("/metrics/appointments-by-day", response_model=AppointmentsByDayResponse)
@router.get("/insights/appointments-by-day", response_model=AppointmentsByDayResponse)
def get_appointments_by_day(
    actor: AnalyticsActor,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    days: Annotated[int, Query(ge=1, le=90)] = 14,
    ends_on: date | None = None,
    doctor_id: UUID | None = None,
) -> AppointmentsByDayResponse:
    return service.get_appointments_by_day(
        actor=actor,
        days=days,
        ends_on=ends_on,
        doctor_id=doctor_id,
    )


@router.get("/analytics/doctor-workload", response_model=DoctorWorkloadResponse)
@router.get("/metrics/doctor-workload", response_model=DoctorWorkloadResponse)
@router.get("/insights/doctor-workload", response_model=DoctorWorkloadResponse)
def get_doctor_workload(
    actor: AnalyticsActor,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    starts_on: date | None = None,
    ends_on: date | None = None,
    doctor_id: UUID | None = None,
) -> DoctorWorkloadResponse:
    return service.get_doctor_workload(
        actor=actor,
        starts_on=starts_on,
        ends_on=ends_on,
        doctor_id=doctor_id,
    )


@router.get("/analytics/appointment-status-breakdown", response_model=AppointmentStatusBreakdownResponse)
@router.get("/metrics/appointment-status-breakdown", response_model=AppointmentStatusBreakdownResponse)
@router.get("/insights/appointment-status-breakdown", response_model=AppointmentStatusBreakdownResponse)
def get_appointment_status_breakdown(
    actor: AnalyticsActor,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    starts_on: date | None = None,
    ends_on: date | None = None,
    doctor_id: UUID | None = None,
) -> AppointmentStatusBreakdownResponse:
    return service.get_appointment_status_breakdown(
        actor=actor,
        starts_on=starts_on,
        ends_on=ends_on,
        doctor_id=doctor_id,
    )
