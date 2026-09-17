"""Notification Router — Solo enruta, delega al Controller."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from composition import get_notification_controller
from modules.auth.presentation.dependencies import get_current_user, require_active_user
from modules.notifications.application.use_cases.cancel_notification import (
    CancelNotificationInput,
)
from modules.notifications.application.use_cases.delete_notification import (
    DeleteNotificationInput,
)
from modules.notifications.application.use_cases.get_notification import (
    GetNotificationInput,
)
from modules.notifications.application.use_cases.list_notifications import (
    ListNotificationsInput,
)
from modules.notifications.application.use_cases.send_notification import (
    SendNotificationInput,
)
from modules.notifications.application.use_cases.update_notification import (
    UpdateNotificationInput,
)
from modules.notifications.presentation.controllers.notification_controller import (
    NotificationController,
)
from modules.notifications.presentation.schemas import (
    CreateNotificationRequestSchema,
    NotificationResponseSchema,
    UpdateNotificationRequestSchema,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])

CurrentUser = Annotated[dict, Depends(get_current_user)]
ActiveUser = Annotated[dict, Depends(require_active_user)]
NotificationCtrl = Annotated[
    NotificationController, Depends(get_notification_controller)
]


@router.post(
    "", response_model=NotificationResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_notification(
    payload: CreateNotificationRequestSchema,
    current_user: CurrentUser,
    controller: NotificationCtrl,
):
    # user_id sale del JWT, nunca del body.
    result = await controller.create(
        payload.to_input_dto(user_id=current_user["user_id"])
    )
    return NotificationResponseSchema(**result)


@router.get("/user/{user_id}", response_model=list[NotificationResponseSchema])
async def list_notifications_by_user(
    user_id: str,
    current_user: CurrentUser,
    controller: NotificationCtrl,
):
    result = await controller.list_by_user(
        ListNotificationsInput(
            user_id=user_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return [NotificationResponseSchema(**item) for item in result]


@router.get("/{notification_id}", response_model=NotificationResponseSchema)
async def get_notification(
    notification_id: str,
    current_user: CurrentUser,
    controller: NotificationCtrl,
):
    result = await controller.get(
        GetNotificationInput(
            notification_id=notification_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return NotificationResponseSchema(**result)


@router.put("/{notification_id}", response_model=NotificationResponseSchema)
async def update_notification(
    notification_id: str,
    payload: UpdateNotificationRequestSchema,
    current_user: ActiveUser,
    controller: NotificationCtrl,
):
    """Solo metadatos y solo en PENDING."""
    result = await controller.update(
        UpdateNotificationInput(
            notification_id=notification_id,
            user_id=current_user["user_id"],
            title=payload.title,
            message=payload.message,
            scheduled_at=payload.scheduled_at,
        )
    )
    return NotificationResponseSchema(**result)


@router.post("/{notification_id}/send", response_model=NotificationResponseSchema)
async def send_notification(
    notification_id: str,
    current_user: ActiveUser,
    controller: NotificationCtrl,
):
    """Transición PENDING → SENT."""
    result = await controller.send(
        SendNotificationInput(
            notification_id=notification_id, user_id=current_user["user_id"]
        )
    )
    return NotificationResponseSchema(**result)


@router.post("/{notification_id}/cancel", response_model=NotificationResponseSchema)
async def cancel_notification(
    notification_id: str,
    current_user: ActiveUser,
    controller: NotificationCtrl,
):
    """Transición PENDING → CANCELLED."""
    result = await controller.cancel(
        CancelNotificationInput(
            notification_id=notification_id, user_id=current_user["user_id"]
        )
    )
    return NotificationResponseSchema(**result)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str,
    current_user: ActiveUser,
    controller: NotificationCtrl,
):
    """Borrado físico: notificaciones efímeras sin referencias."""
    await controller.delete(
        DeleteNotificationInput(
            notification_id=notification_id, user_id=current_user["user_id"]
        )
    )
