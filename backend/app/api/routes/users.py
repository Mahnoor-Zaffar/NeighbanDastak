from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps.permissions import CurrentActor, require_roles
from app.core.rbac import Role
from app.db.session import get_db_session
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserListResponse, UserRead

router = APIRouter(prefix="/users", tags=["users"])

AdminActor = Annotated[CurrentActor, Depends(require_roles(Role.ADMIN))]


def get_user_repository(session: Annotated[Session, Depends(get_db_session)]) -> UserRepository:
    return UserRepository(session)


@router.get("", response_model=UserListResponse)
def list_users(
    _: AdminActor,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
    role: Role | None = None,
    is_active: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> UserListResponse:
    items, total = repository.list(
        role=role,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return UserListResponse(
        items=[UserRead.model_validate(u) for u in items],
        total=total,
    )


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    _: AdminActor,
    user_id: UUID,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserRead:
    user = repository.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserRead.model_validate(user)


@router.post("/{user_id}/activate", response_model=UserRead)
def activate_user(
    _: AdminActor,
    user_id: UUID,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserRead:
    user = repository.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already active")
    user.is_active = True
    repository.commit()
    return UserRead.model_validate(user)


@router.post("/{user_id}/deactivate", response_model=UserRead)
def deactivate_user(
    _: AdminActor,
    user_id: UUID,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserRead:
    user = repository.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already inactive")
    user.is_active = False
    repository.commit()
    return UserRead.model_validate(user)
