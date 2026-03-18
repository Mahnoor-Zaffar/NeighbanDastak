from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps.permissions import CurrentActor, require_roles
from app.core.rbac import Role
from app.db.session import get_db_session
from app.schemas.prescription import (
    PrescriptionCreate,
    PrescriptionListResponse,
    PrescriptionRead,
    PrescriptionUpdate,
)
from app.services.audit_service import AuditContext
from app.services.prescription_service import PrescriptionService

router = APIRouter(tags=["prescriptions"])

AllowedActor = Annotated[CurrentActor, Depends(require_roles(Role.ADMIN, Role.DOCTOR))]


def get_prescription_service(session: Annotated[Session, Depends(get_db_session)]) -> PrescriptionService:
    return PrescriptionService(session)


@router.post("/prescriptions", response_model=PrescriptionRead, status_code=status.HTTP_201_CREATED)
def create_prescription(
    actor: AllowedActor,
    request: Request,
    payload: PrescriptionCreate,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
) -> PrescriptionRead:
    return service.create_prescription(
        payload,
        context=AuditContext(
            actor_role=actor.role.value,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )


@router.get("/prescriptions/{prescription_id}", response_model=PrescriptionRead)
def get_prescription(
    _: AllowedActor,
    prescription_id: UUID,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
) -> PrescriptionRead:
    return service.get_prescription(prescription_id)


@router.get("/patients/{patient_id}/prescriptions", response_model=PrescriptionListResponse)
def list_patient_prescriptions(
    _: AllowedActor,
    patient_id: UUID,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PrescriptionListResponse:
    return service.list_by_patient(
        patient_id=patient_id,
        limit=limit,
        offset=offset,
    )


@router.get("/visits/{visit_id}/prescriptions", response_model=PrescriptionListResponse)
def list_visit_prescriptions(
    _: AllowedActor,
    visit_id: UUID,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PrescriptionListResponse:
    return service.list_by_visit(
        visit_id=visit_id,
        limit=limit,
        offset=offset,
    )


@router.put("/prescriptions/{prescription_id}", response_model=PrescriptionRead)
def update_prescription(
    actor: AllowedActor,
    request: Request,
    prescription_id: UUID,
    payload: PrescriptionUpdate,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
) -> PrescriptionRead:
    return service.update_prescription(
        prescription_id,
        payload,
        context=AuditContext(
            actor_role=actor.role.value,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )


@router.delete("/prescriptions/{prescription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prescription(
    actor: AllowedActor,
    request: Request,
    prescription_id: UUID,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
) -> Response:
    service.delete_prescription(
        prescription_id,
        context=AuditContext(
            actor_role=actor.role.value,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
