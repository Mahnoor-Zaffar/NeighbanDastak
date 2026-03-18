from collections.abc import Callable
from typing import Literal
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.core.rbac import Role

DEMO_ROLE_HEADER = "X-Demo-Role"
DEMO_USER_ID_HEADER = "X-Demo-User-Id"
QueueRole = Literal["admin", "doctor", "receptionist"]
QUEUE_ALLOWED_ROLES: set[QueueRole] = {"admin", "doctor", "receptionist"}


class CurrentActor(BaseModel):
    role: Role


class QueueActor(BaseModel):
    role: QueueRole
    user_id: UUID | None = None


def get_current_actor(
    x_demo_role: Annotated[str | None, Header(alias=DEMO_ROLE_HEADER)] = None,
) -> CurrentActor:
    if x_demo_role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing {DEMO_ROLE_HEADER} header",
        )

    try:
        return CurrentActor(role=Role(x_demo_role.lower()))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unsupported role",
        ) from exc


def get_queue_actor(
    x_demo_role: Annotated[str | None, Header(alias=DEMO_ROLE_HEADER)] = None,
    x_demo_user_id: Annotated[str | None, Header(alias=DEMO_USER_ID_HEADER)] = None,
) -> QueueActor:
    if x_demo_role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing {DEMO_ROLE_HEADER} header",
        )

    normalized_role = x_demo_role.lower()
    if normalized_role not in QUEUE_ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unsupported role",
        )

    parsed_user_id: UUID | None = None
    if x_demo_user_id is not None:
        try:
            parsed_user_id = UUID(x_demo_user_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Invalid {DEMO_USER_ID_HEADER} header",
            ) from exc

    return QueueActor(role=normalized_role, user_id=parsed_user_id)


def require_roles(*allowed_roles: Role) -> Callable[[CurrentActor], CurrentActor]:
    def dependency(actor: Annotated[CurrentActor, Depends(get_current_actor)]) -> CurrentActor:
        if actor.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return actor

    return dependency
