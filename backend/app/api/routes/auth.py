from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps.permissions import QueueActor, get_queue_actor
from app.db.session import get_db_session
from app.schemas.auth import (
    DemoCurrentUserResponse,
    DemoDoctorProfileListResponse,
    DemoLoginRequest,
)
from app.services.demo_auth_service import DemoAuthService

router = APIRouter(prefix="/auth/demo", tags=["auth"])

AuthActor = Annotated[QueueActor, Depends(get_queue_actor)]


def get_demo_auth_service(session: Annotated[Session, Depends(get_db_session)]) -> DemoAuthService:
    return DemoAuthService(session)


@router.get("/doctors", response_model=DemoDoctorProfileListResponse)
def list_demo_doctors(
    service: Annotated[DemoAuthService, Depends(get_demo_auth_service)],
) -> DemoDoctorProfileListResponse:
    return service.list_doctor_profiles()


@router.post("/login", response_model=DemoCurrentUserResponse)
def login_demo_user(
    payload: DemoLoginRequest,
    service: Annotated[DemoAuthService, Depends(get_demo_auth_service)],
) -> DemoCurrentUserResponse:
    return service.login(payload)


@router.get("/current-user", response_model=DemoCurrentUserResponse)
def get_demo_current_user(
    actor: AuthActor,
    service: Annotated[DemoAuthService, Depends(get_demo_auth_service)],
) -> DemoCurrentUserResponse:
    return service.get_current_user(actor)
