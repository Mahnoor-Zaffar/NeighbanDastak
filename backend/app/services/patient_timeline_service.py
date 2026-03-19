from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps.permissions import QueueActor
from app.db.models.appointment import Appointment, AppointmentStatus
from app.db.models.audit_log import AuditLog
from app.db.models.prescription import Prescription
from app.db.models.visit import Visit
from app.repositories.timeline_repository import TimelineRepository
from app.schemas.timeline import PatientTimelineEvent, PatientTimelineResponse

STATUS_EVENT_TYPE_BY_VALUE = {
    "completed": "appointment_completed",
    "cancelled": "appointment_cancelled",
    "no_show": "appointment_no_show",
}

STATUS_TITLE_BY_VALUE = {
    "completed": "Appointment completed",
    "cancelled": "Appointment cancelled",
    "no_show": "Appointment marked no-show",
}


class PatientTimelineService:
    def __init__(self, session: Session):
        self.repository = TimelineRepository(session)

    def get_timeline(self, patient_id: UUID, *, actor: QueueActor) -> PatientTimelineResponse:
        patient = self.repository.get_patient(patient_id)
        if patient is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        self._authorize_timeline_access(actor=actor, patient_id=patient_id)

        events: list[PatientTimelineEvent] = []
        patient_created_log = self.repository.get_patient_created_log(patient_id)
        if patient_created_log is not None:
            events.append(
                PatientTimelineEvent(
                    id=f"patient_created:{patient_id}",
                    event_type="patient_created",
                    event_timestamp=patient_created_log.occurred_at,
                    title="Patient profile created",
                    subtitle=f"{patient.first_name} {patient.last_name} ({patient.record_number})",
                    actor_name=self._format_actor_role(patient_created_log.actor_role),
                    related_entity_type="patient",
                    related_entity_id=str(patient_id),
                    metadata={"record_number": patient.record_number},
                )
            )

        appointments = self.repository.list_appointments_for_patient(patient_id)
        events.extend(self._build_appointment_events(appointments))

        visits = self.repository.list_visits_for_patient(patient_id)
        events.extend(self._build_visit_events(visits))

        prescriptions = self.repository.list_prescriptions_for_patient(patient_id)
        events.extend(self._build_prescription_events(prescriptions))

        sorted_events = sorted(
            events,
            key=lambda event: (event.event_timestamp, event.id),
            reverse=True,
        )
        return PatientTimelineResponse(
            patient_id=str(patient_id),
            sort_order="desc",
            items=sorted_events,
            total=len(sorted_events),
        )

    def _build_appointment_events(self, appointments: list[Appointment]) -> list[PatientTimelineEvent]:
        if not appointments:
            return []

        events: list[PatientTimelineEvent] = []
        status_logs = self.repository.list_appointment_status_change_logs([appointment.id for appointment in appointments])
        appointment_status_log_counts: dict[UUID, int] = {}
        for log in status_logs:
            if log.resource_id is None:
                continue

            to_status = str((log.metadata_json or {}).get("to_status", "")).strip()
            event_type = STATUS_EVENT_TYPE_BY_VALUE.get(to_status)
            title = STATUS_TITLE_BY_VALUE.get(to_status)
            if event_type is None or title is None:
                continue

            appointment_status_log_counts[log.resource_id] = appointment_status_log_counts.get(log.resource_id, 0) + 1
            events.append(
                PatientTimelineEvent(
                    id=f"{event_type}:{log.resource_id}:{log.id}",
                    event_type=event_type,
                    event_timestamp=log.occurred_at,
                    title=title,
                    subtitle=self._format_status_transition(log),
                    actor_name=self._format_actor_role(log.actor_role),
                    related_entity_type="appointment",
                    related_entity_id=str(log.resource_id),
                    metadata=log.metadata_json or {},
                )
            )

        for appointment in appointments:
            events.append(
                PatientTimelineEvent(
                    id=f"appointment_scheduled:{appointment.id}",
                    event_type="appointment_scheduled",
                    event_timestamp=appointment.created_at,
                    title="Appointment scheduled",
                    subtitle=f"For {appointment.scheduled_for.isoformat()}",
                    actor_name=None,
                    related_entity_type="appointment",
                    related_entity_id=str(appointment.id),
                    metadata={
                        "scheduled_for": appointment.scheduled_for.isoformat(),
                        "reason": appointment.reason,
                        "status": appointment.status.value,
                    },
                )
            )

            if (
                appointment.status in {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW}
                and appointment_status_log_counts.get(appointment.id, 0) == 0
            ):
                status_value = appointment.status.value
                event_type = STATUS_EVENT_TYPE_BY_VALUE[status_value]
                events.append(
                    PatientTimelineEvent(
                        id=f"{event_type}:{appointment.id}:fallback",
                        event_type=event_type,
                        event_timestamp=appointment.updated_at,
                        title=STATUS_TITLE_BY_VALUE[status_value],
                        subtitle="Current appointment status",
                        actor_name=None,
                        related_entity_type="appointment",
                        related_entity_id=str(appointment.id),
                        metadata={"status": status_value, "source": "appointment_record"},
                    )
                )

        return events

    def _build_visit_events(self, visits: list[Visit]) -> list[PatientTimelineEvent]:
        events: list[PatientTimelineEvent] = []
        for visit in visits:
            events.append(
                PatientTimelineEvent(
                    id=f"visit_created:{visit.id}",
                    event_type="visit_created",
                    event_timestamp=visit.created_at,
                    title="Visit recorded",
                    subtitle=visit.diagnosis_summary or visit.complaint,
                    actor_name=None,
                    related_entity_type="visit",
                    related_entity_id=str(visit.id),
                    metadata={"appointment_id": str(visit.appointment_id) if visit.appointment_id else None},
                )
            )
        return events

    def _build_prescription_events(self, prescriptions: list[Prescription]) -> list[PatientTimelineEvent]:
        if not prescriptions:
            return []

        doctor_map = self.repository.get_users_by_ids([prescription.doctor_id for prescription in prescriptions])
        item_counts = self.repository.get_prescription_item_counts([prescription.id for prescription in prescriptions])
        events: list[PatientTimelineEvent] = []
        for prescription in prescriptions:
            doctor = doctor_map.get(prescription.doctor_id)
            events.append(
                PatientTimelineEvent(
                    id=f"prescription_created:{prescription.id}",
                    event_type="prescription_created",
                    event_timestamp=prescription.created_at,
                    title="Prescription created",
                    subtitle=prescription.diagnosis_summary,
                    actor_name=doctor.full_name if doctor else None,
                    related_entity_type="prescription",
                    related_entity_id=str(prescription.id),
                    metadata={
                        "doctor_id": str(prescription.doctor_id),
                        "visit_id": str(prescription.visit_id),
                        "item_count": item_counts.get(prescription.id, 0),
                    },
                )
            )
        return events

    def _format_status_transition(self, log: AuditLog) -> str:
        metadata = log.metadata_json or {}
        from_status = metadata.get("from_status")
        to_status = metadata.get("to_status")
        if from_status and to_status:
            return f"Status changed from {from_status} to {to_status}"
        return "Appointment status updated"

    def _format_actor_role(self, actor_role: str | None) -> str | None:
        if not actor_role:
            return None
        return actor_role.replace("_", " ").title()

    def _authorize_timeline_access(self, *, actor: QueueActor, patient_id: UUID) -> None:
        if actor.role in {"admin", "receptionist"}:
            return

        if actor.role != "doctor":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        if actor.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor identity is required",
            )

        doctor = self.repository.get_active_doctor(actor.user_id)
        if doctor is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

        if not self.repository.doctor_has_patient_access(doctor_id=actor.user_id, patient_id=patient_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctors can only view timelines for their assigned patients",
            )
