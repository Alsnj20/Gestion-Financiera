"""AuditLog Router — Solo enruta, delega al Controller (append-only)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from composition import get_audit_log_controller
from modules.audit_logs.application.use_cases.list_audit_logs import ListAuditLogsInput
from modules.audit_logs.presentation.controllers.audit_log_controller import (
    AuditLogController,
)
from modules.audit_logs.presentation.schemas import (
    AuditLogResponseSchema,
    CreateAuditLogRequestSchema,
)
from modules.auth.presentation.dependencies import get_current_user

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])

CurrentUser = Annotated[dict, Depends(get_current_user)]
AuditLogCtrl = Annotated[AuditLogController, Depends(get_audit_log_controller)]


@router.post(
    "", response_model=AuditLogResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_audit_log(
    payload: CreateAuditLogRequestSchema,
    current_user: CurrentUser,
    controller: AuditLogCtrl,
):
    # user_id sale del JWT, nunca del body.
    result = await controller.create(
        payload.to_input_dto(user_id=current_user["user_id"])
    )
    return AuditLogResponseSchema(**result)


@router.get("/user/{user_id}", response_model=list[AuditLogResponseSchema])
async def list_audit_logs_by_user(
    user_id: str,
    current_user: CurrentUser,
    controller: AuditLogCtrl,
):
    result = await controller.list_by_user(
        ListAuditLogsInput(
            user_id=user_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return [AuditLogResponseSchema(**item) for item in result]
