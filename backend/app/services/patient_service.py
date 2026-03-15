from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.patient import Patient
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import PatientCreate, PatientListResponse, PatientRead, PatientUpdate
from app.services.audit_service import AuditContext, AuditService


class PatientService:
    def __init__(self, session: Session):
        self.repository = PatientRepository(session)
        self.audit = AuditService(session)

    def list_patients(
        self,
        *,
        search: str | None,
        include_archived: bool,
        limit: int,
        offset: int,
    ) -> PatientListResponse:
        items, total = self.repository.list(
            search=search,
            include_archived=include_archived,
            limit=limit,
            offset=offset,
        )
        return PatientListResponse(items=[PatientRead.model_validate(item) for item in items], total=total)

    def get_patient(self, patient_id: UUID) -> PatientRead:
        patient = self.repository.get_by_id(patient_id)
        if patient is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

        return PatientRead.model_validate(patient)

    def create_patient(self, payload: PatientCreate, *, context: AuditContext) -> PatientRead:
        record_number = payload.record_number or self._generate_record_number()
        self._ensure_record_number_available(record_number)

        patient = Patient(
            record_number=record_number,
            first_name=payload.first_name,
            last_name=payload.last_name,
            date_of_birth=payload.date_of_birth,
            email=str(payload.email) if payload.email else None,
            phone=payload.phone,
            city=payload.city,
            notes=payload.notes,
        )
        patient = self.repository.create(patient)
        self.audit.log_action(
            context=context,
            action="patient.create",
            resource_type="patient",
            resource_id=patient.id,
            metadata={"record_number": patient.record_number},
        )
        self.repository.commit()
        return PatientRead.model_validate(patient)

    def update_patient(self, patient_id: UUID, payload: PatientUpdate, *, context: AuditContext) -> PatientRead:
        patient = self.repository.get_by_id(patient_id)
        if patient is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

        updates = payload.model_dump(exclude_unset=True)
        if "record_number" in updates and updates["record_number"] != patient.record_number:
            self._ensure_record_number_available(updates["record_number"])

        for field, value in updates.items():
            if field == "email" and value is not None:
                value = str(value)
            setattr(patient, field, value)

        self.audit.log_action(
            context=context,
            action="patient.update",
            resource_type="patient",
            resource_id=patient.id,
            metadata={"changed_fields": sorted(updates.keys())},
        )
        self.repository.commit()
        return PatientRead.model_validate(patient)

    def archive_patient(self, patient_id: UUID, *, context: AuditContext) -> PatientRead:
        patient = self.repository.get_by_id(patient_id)
        if patient is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        if patient.archived_at is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Patient is already archived")

        patient.archived_at = datetime.now(UTC)
        self.audit.log_action(
            context=context,
            action="patient.archive",
            resource_type="patient",
            resource_id=patient.id,
        )
        self.repository.commit()
        return PatientRead.model_validate(patient)

    def _ensure_record_number_available(self, record_number: str) -> None:
        existing_patient = self.repository.get_by_record_number(record_number)
        if existing_patient is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="record_number already exists",
            )

    def _generate_record_number(self) -> str:
        while True:
            candidate = f"PAT-{uuid4().hex[:8].upper()}"
            if self.repository.get_by_record_number(candidate) is None:
                return candidate
