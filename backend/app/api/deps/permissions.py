from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.core.rbac import Role

DEMO_ROLE_HEADER = "X-Demo-Role"


class CurrentActor(BaseModel):
    role: Role


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


def require_roles(*allowed_roles: Role) -> Callable[[CurrentActor], CurrentActor]:
    def dependency(actor: Annotated[CurrentActor, Depends(get_current_actor)]) -> CurrentActor:
        if actor.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return actor

    return dependency
