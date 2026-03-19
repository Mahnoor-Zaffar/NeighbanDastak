from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps.permissions import QueueActor
from app.core.rbac import Role
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    DemoCurrentUserResponse,
    DemoDoctorProfileListResponse,
    DemoDoctorProfileRead,
    DemoLoginRequest,
)


class DemoAuthService:
    def __init__(self, session: Session):
        self.users = UserRepository(session)

    def list_doctor_profiles(self) -> DemoDoctorProfileListResponse:
        doctors = self.users.list_active_doctors()
        items = [
            DemoDoctorProfileRead(
                id=doctor.id,
                full_name=doctor.full_name,
                email=doctor.email,
                specialty=doctor.specialty,
            )
            for doctor in doctors
        ]
        return DemoDoctorProfileListResponse(items=items, total=len(items))

    def login(self, payload: DemoLoginRequest) -> DemoCurrentUserResponse:
        if payload.role != Role.DOCTOR:
            return DemoCurrentUserResponse(
                role=payload.role,
                user_id=None,
                doctor_profile_id=None,
                full_name=None,
                email=None,
            )

        doctor = None
        if payload.doctor_profile_id is not None:
            doctor = self.users.get_active_doctor_by_id(payload.doctor_profile_id)
        else:
            doctor = self.users.get_first_active_doctor()

        if doctor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor profile not found",
            )

        return DemoCurrentUserResponse(
            role=Role.DOCTOR,
            user_id=doctor.id,
            doctor_profile_id=doctor.id,
            full_name=doctor.full_name,
            email=doctor.email,
        )

    def get_current_user(self, actor: QueueActor) -> DemoCurrentUserResponse:
        if actor.role != "doctor":
            normalized_role = Role(actor.role)
            return DemoCurrentUserResponse(
                role=normalized_role,
                user_id=None,
                doctor_profile_id=None,
                full_name=None,
                email=None,
            )

        if actor.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor profile is not linked to the current session",
            )

        doctor = self.users.get_active_doctor_by_id(actor.user_id)
        if doctor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor profile not found",
            )

        return DemoCurrentUserResponse(
            role=Role.DOCTOR,
            user_id=doctor.id,
            doctor_profile_id=doctor.id,
            full_name=doctor.full_name,
            email=doctor.email,
        )
