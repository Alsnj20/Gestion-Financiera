"""Limit Router — Solo enruta, delega al Controller."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from composition import get_limit_controller
from modules.auth.presentation.dependencies import get_current_user, require_active_user
from modules.limits.application.use_cases.archive_limit import ArchiveLimitInput
from modules.limits.application.use_cases.get_limit import GetLimitInput
from modules.limits.application.use_cases.list_limits import ListLimitsInput
from modules.limits.application.use_cases.restore_limit import RestoreLimitInput
from modules.limits.application.use_cases.update_limit import UpdateLimitInput
from modules.limits.presentation.controllers.limit_controller import LimitController
from modules.limits.presentation.schemas import (
    CreateLimitRequestSchema,
    LimitResponseSchema,
    UpdateLimitRequestSchema,
)

router = APIRouter(prefix="/limits", tags=["limits"])

CurrentUser = Annotated[dict, Depends(get_current_user)]
ActiveUser = Annotated[dict, Depends(require_active_user)]
LimitCtrl = Annotated[LimitController, Depends(get_limit_controller)]


@router.post(
    "", response_model=LimitResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_limit(
    payload: CreateLimitRequestSchema,
    current_user: CurrentUser,
    controller: LimitCtrl,
):
    # user_id sale del JWT, nunca del body.
    result = await controller.create(
        payload.to_input_dto(user_id=current_user["user_id"])
    )
    return LimitResponseSchema(**result)


@router.get("/user/{user_id}", response_model=list[LimitResponseSchema])
async def list_limits_by_user(
    user_id: str,
    current_user: CurrentUser,
    controller: LimitCtrl,
    include_archived: bool = Query(default=False),
):
    result = await controller.list_by_user(
        ListLimitsInput(
            user_id=user_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
            include_archived=include_archived,
        )
    )
    return [LimitResponseSchema(**item) for item in result]


@router.get("/{limit_id}", response_model=LimitResponseSchema)
async def get_limit(
    limit_id: str,
    current_user: CurrentUser,
    controller: LimitCtrl,
):
    result = await controller.get(
        GetLimitInput(
            limit_id=limit_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return LimitResponseSchema(**result)


@router.put("/{limit_id}", response_model=LimitResponseSchema)
async def update_limit(
    limit_id: str,
    payload: UpdateLimitRequestSchema,
    current_user: ActiveUser,
    controller: LimitCtrl,
):
    result = await controller.update(
        UpdateLimitInput(
            limit_id=limit_id,
            user_id=current_user["user_id"],
            name=payload.name,
            amount=payload.amount,
            period_type=payload.period_type,
            category_id=payload.category_id,
            threshold_warning=payload.threshold_warning,
        )
    )
    return LimitResponseSchema(**result)


@router.delete("/{limit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_limit(
    limit_id: str,
    current_user: ActiveUser,
    controller: LimitCtrl,
):
    """Archivado lógico; nunca borrado físico."""
    await controller.archive(
        ArchiveLimitInput(limit_id=limit_id, user_id=current_user["user_id"])
    )


@router.post("/{limit_id}/restore", response_model=LimitResponseSchema)
async def restore_limit(
    limit_id: str,
    current_user: ActiveUser,
    controller: LimitCtrl,
):
    result = await controller.restore(
        RestoreLimitInput(limit_id=limit_id, user_id=current_user["user_id"])
    )
    return LimitResponseSchema(**result)
