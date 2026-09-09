from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from composition import get_user_controller
from modules.auth.presentation.dependencies import (
    get_current_user,
    require_active_admin,
    require_admin,
)
from modules.users.application.use_cases.delete_user import DeleteUserInput
from modules.users.application.use_cases.get_user import GetUserInput
from modules.users.application.use_cases.list_users import ListUsersInput
from modules.users.application.use_cases.update_user import UpdateUserInput
from modules.users.presentation.controllers.user_controller import UserController
from modules.users.presentation.schemas import (
    UpdateUserRequestSchema,
    UserResponseSchema,
)

router = APIRouter(prefix="/users", tags=["users"])

CurrentUser = Annotated[dict, Depends(get_current_user)]
AdminUser = Annotated[dict, Depends(require_admin)]
ActiveAdmin = Annotated[dict, Depends(require_active_admin)]
UserCtrl = Annotated[UserController, Depends(get_user_controller)]


@router.get("", response_model=list[UserResponseSchema])
async def list_users(
    current_user: AdminUser,
    controller: UserCtrl,
):
    """Directorio de usuarios: solo admin (solo lectura)."""
    result = await controller.list_all(
        ListUsersInput(
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return [UserResponseSchema(**item) for item in result]


@router.get("/{user_id}", response_model=UserResponseSchema)
async def get_user(
    user_id: str,
    current_user: CurrentUser,
    controller: UserCtrl,
):
    result = await controller.get(
        GetUserInput(
            user_id=user_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return UserResponseSchema(**result)


@router.put("/{user_id}", response_model=UserResponseSchema)
async def update_user(
    user_id: str,
    payload: UpdateUserRequestSchema,
    current_user: CurrentUser,
    controller: UserCtrl,
):
    result = await controller.update(
        UpdateUserInput(
            user_id=user_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
            name=payload.name,
            email=payload.email,
            timezone=payload.timezone,
            currency=payload.currency,
        )
    )
    return UserResponseSchema(**result)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: ActiveAdmin,
    controller: UserCtrl,
):
    """Borrado total (CASCADE): solo admin verificado en DB, vía solicitud GDPR."""
    await controller.delete(
        DeleteUserInput(
            user_id=user_id,
            requester_role=current_user.get("role", "USER"),
        )
    )
