"""Account Router — Solo enruta, delega al Controller.

Rutas propias: /accounts (dueño).
Rutas anidadas: /users/{user_id}/accounts (dueño o admin, solo lectura).
El anidado vive en este módulo para mantener independencia entre módulos.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from composition import get_account_controller
from modules.accounts.application.use_cases.archive_account import ArchiveAccountInput
from modules.accounts.application.use_cases.get_account import GetAccountInput
from modules.accounts.application.use_cases.list_accounts import ListAccountsByUserInput
from modules.accounts.application.use_cases.restore_account import RestoreAccountInput
from modules.accounts.application.use_cases.update_account import UpdateAccountInput
from modules.accounts.presentation.controllers.account_controller import (
    AccountController,
)
from modules.accounts.presentation.schemas import (
    AccountResponseSchema,
    CreateAccountRequestSchema,
    UpdateAccountRequestSchema,
)
from modules.auth.presentation.dependencies import get_current_user

# ---- Routers ----
router = APIRouter(prefix="/accounts", tags=["accounts"])
user_accounts_router = APIRouter(prefix="/users/{user_id}/accounts", tags=["accounts"])
CurrentUser = Annotated[dict, Depends(get_current_user)]
AccountCtrl = Annotated[AccountController, Depends(get_account_controller)]


@router.post(
    "",
    response_model=AccountResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_account(
    payload: CreateAccountRequestSchema,
    current_user: CurrentUser,
    controller: AccountCtrl,
):
    result = await controller.create(
        payload.to_input_dto(user_id=current_user["user_id"])
    )

    return AccountResponseSchema(**result)


@router.get(
    "",
    response_model=list[AccountResponseSchema],
)
async def list_my_accounts(
    current_user: CurrentUser,
    controller: AccountCtrl,
    include_archived: bool = Query(default=False),
):
    """Mis cuentas (user_id sale del JWT)."""
    result = await controller.list_by_user(
        ListAccountsByUserInput(
            user_id=current_user["user_id"],
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
            include_archived=include_archived,
        )
    )

    return [AccountResponseSchema(**item) for item in result]


@user_accounts_router.get(
    "",
    response_model=list[AccountResponseSchema],
)
async def list_user_accounts(
    user_id: str,
    current_user: CurrentUser,
    controller: AccountCtrl,
    include_archived: bool = Query(default=False),
):
    """Cuentas de un usuario: dueño o admin (solo lectura)."""
    result = await controller.list_by_user(
        ListAccountsByUserInput(
            user_id=user_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
            include_archived=include_archived,
        )
    )

    return [AccountResponseSchema(**item) for item in result]


@router.get(
    "/{account_id}",
    response_model=AccountResponseSchema,
)
async def get_account(
    account_id: str,
    current_user: CurrentUser,
    controller: AccountCtrl,
):
    result = await controller.get(
        GetAccountInput(
            account_id=account_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )

    return AccountResponseSchema(**result)


@router.put(
    "/{account_id}",
    response_model=AccountResponseSchema,
)
async def update_account(
    account_id: str,
    payload: UpdateAccountRequestSchema,
    current_user: CurrentUser,
    controller: AccountCtrl,
):
    result = await controller.update(
        UpdateAccountInput(
            account_id=account_id,
            user_id=current_user["user_id"],
            name=payload.name,
            type=payload.type,
            is_default=payload.is_default,
        )
    )

    return AccountResponseSchema(**result)


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def archive_account(
    account_id: str,
    current_user: CurrentUser,
    controller: AccountCtrl,
):
    await controller.archive(
        ArchiveAccountInput(account_id=account_id, user_id=current_user["user_id"])
    )


@router.post(
    "/{account_id}/restore",
    response_model=AccountResponseSchema,
)
async def restore_account(
    account_id: str,
    current_user: CurrentUser,
    controller: AccountCtrl,
):
    result = await controller.restore(
        RestoreAccountInput(account_id=account_id, user_id=current_user["user_id"])
    )

    return AccountResponseSchema(**result)
