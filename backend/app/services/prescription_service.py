from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.rbac import Role
from app.db.models.prescription import Prescription, PrescriptionItem
from app.repositories.patient_repository import PatientRepository
from app.repositories.prescription_repository import PrescriptionRepository
from app.repositories.user_repository import UserRepository
from app.repositories.visit_repository import VisitRepository
from app.schemas.prescription import (
    PrescriptionCreate,
    PrescriptionItemRead,
    PrescriptionListResponse,
    PrescriptionRead,
    PrescriptionUpdate,
)
from app.services.audit_service import AuditContext, AuditService


class PrescriptionService:
    def __init__(self, session: Session):
        self.prescriptions = PrescriptionRepository(session)
        self.patients = PatientRepository(session)
        self.visits = VisitRepository(session)
        self.users = UserRepository(session)
        self.audit = AuditService(session)

    def create_prescription(self, payload: PrescriptionCreate, *, context: AuditContext) -> PrescriptionRead:
        self._validate_patient_for_creation(payload.patient_id)
        self._validate_visit_link(payload.patient_id, payload.visit_id)
        self._validate_doctor(payload.doctor_id)

        prescription = Prescription(
            patient_id=payload.patient_id,
            visit_id=payload.visit_id,
            doctor_id=payload.doctor_id,
            diagnosis_summary=payload.diagnosis_summary,
            notes=payload.notes,
        )
        prescription = self.prescriptions.create(prescription)
        items = self.prescriptions.create_items(
            [
                PrescriptionItem(
                    prescription_id=prescription.id,
                    medicine_name=item.medicine_name,
                    dosage=item.dosage,
                    frequency=item.frequency,
                    duration=item.duration,
                    instructions=item.instructions,
                )
                for item in payload.items
            ]
        )

        self.audit.log_action(
            context=context,
            action="prescription.create",
            resource_type="prescription",
            resource_id=prescription.id,
            metadata={"item_count": len(items), "visit_id": str(prescription.visit_id)},
        )
        self.prescriptions.commit()
        return self._build_prescription_read(prescription, items)

    def get_prescription(self, prescription_id: UUID) -> PrescriptionRead:
        prescription = self.prescriptions.get_by_id(prescription_id)
        if prescription is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")

        items = self.prescriptions.list_items_by_prescription_id(prescription.id)
        return self._build_prescription_read(prescription, items)

    def list_by_patient(
        self,
        *,
        patient_id: UUID,
        limit: int,
        offset: int,
    ) -> PrescriptionListResponse:
        patient = self.patients.get_by_id(patient_id)
        if patient is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

        prescriptions, total = self.prescriptions.list_by_patient(patient_id=patient_id, limit=limit, offset=offset)
        items_map = self.prescriptions.list_items_by_prescription_ids([item.id for item in prescriptions])
        return PrescriptionListResponse(
            items=[
                self._build_prescription_read(prescription, items_map.get(prescription.id, []))
                for prescription in prescriptions
            ],
            total=total,
        )

    def list_by_visit(
        self,
        *,
        visit_id: UUID,
        limit: int,
        offset: int,
    ) -> PrescriptionListResponse:
        visit = self.visits.get_by_id(visit_id)
        if visit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")

        prescriptions, total = self.prescriptions.list_by_visit(visit_id=visit_id, limit=limit, offset=offset)
        items_map = self.prescriptions.list_items_by_prescription_ids([item.id for item in prescriptions])
        return PrescriptionListResponse(
            items=[
                self._build_prescription_read(prescription, items_map.get(prescription.id, []))
                for prescription in prescriptions
            ],
            total=total,
        )

    def update_prescription(
        self,
        prescription_id: UUID,
        payload: PrescriptionUpdate,
        *,
        context: AuditContext,
    ) -> PrescriptionRead:
        prescription = self.prescriptions.get_by_id(prescription_id)
        if prescription is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")

        prescription.diagnosis_summary = payload.diagnosis_summary
        prescription.notes = payload.notes
        self.prescriptions.delete_items_by_prescription_id(prescription.id)
        items = self.prescriptions.create_items(
            [
                PrescriptionItem(
                    prescription_id=prescription.id,
                    medicine_name=item.medicine_name,
                    dosage=item.dosage,
                    frequency=item.frequency,
                    duration=item.duration,
                    instructions=item.instructions,
                )
                for item in payload.items
            ]
        )

        self.audit.log_action(
            context=context,
            action="prescription.update",
            resource_type="prescription",
            resource_id=prescription.id,
            metadata={"item_count": len(items)},
        )
        self.prescriptions.commit()
        return self._build_prescription_read(prescription, items)

    def delete_prescription(self, prescription_id: UUID, *, context: AuditContext) -> None:
        prescription = self.prescriptions.get_by_id(prescription_id)
        if prescription is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")

        self.prescriptions.delete_items_by_prescription_id(prescription.id)
        self.prescriptions.delete(prescription)
        self.audit.log_action(
            context=context,
            action="prescription.delete",
            resource_type="prescription",
            resource_id=prescription.id,
        )
        self.prescriptions.commit()

    def _validate_patient_for_creation(self, patient_id: UUID) -> None:
        patient = self.patients.get_by_id(patient_id)
        if patient is None or patient.archived_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    def _validate_visit_link(self, patient_id: UUID, visit_id: UUID) -> None:
        visit = self.visits.get_by_id(visit_id)
        if visit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
        if visit.patient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="visit does not belong to the provided patient",
            )

    def _validate_doctor(self, doctor_id: UUID) -> None:
        user = self.users.get_by_id(doctor_id)
        if user is None or user.role != Role.DOCTOR or not user.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    def _build_prescription_read(
        self,
        prescription: Prescription,
        prescription_items: list[PrescriptionItem],
    ) -> PrescriptionRead:
        return PrescriptionRead(
            id=prescription.id,
            patient_id=prescription.patient_id,
            visit_id=prescription.visit_id,
            doctor_id=prescription.doctor_id,
            diagnosis_summary=prescription.diagnosis_summary,
            notes=prescription.notes,
            items=[PrescriptionItemRead.model_validate(item) for item in prescription_items],
            created_at=prescription.created_at,
            updated_at=prescription.updated_at,
        )
