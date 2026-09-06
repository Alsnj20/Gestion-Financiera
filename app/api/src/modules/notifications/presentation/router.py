from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_notification_use_case, build_notification_repository
from modules.auth.presentation.dependencies import get_current_user, check_ownership
from infrastructure.database.session import get_session
from modules.notifications.presentation.schemas import CreateNotificationRequestSchema, UpdateNotificationRequestSchema, NotificationResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("", response_model=NotificationResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_notification(payload: CreateNotificationRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    use_case = build_create_notification_use_case(session)
    try:
        input_dto = payload.to_input_dto()
        input_dto.user_id = current_user["user_id"]
        result = await use_case.execute(input_dto)
        await session.commit()
        return NotificationResponseSchema(id=result.id, user_id=result.user_id, type=result.type, title=result.title, message=result.message, status=result.status)
    except (ValidationError, ValueError) as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "VALIDATION_ERROR", "message": str(e)}) from e
    except ConflictError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": e.code, "message": e.message}) from e


@router.get("/user/{user_id}", response_model=list[NotificationResponseSchema])
async def list_notifications_by_user(user_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    if user_id != current_user["user_id"] and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    repo = build_notification_repository(session)
    notifications = await repo.find_by_user(user_id)
    return [NotificationResponseSchema(id=n.id, user_id=n.user_id, type=n.type, title=n.title, message=n.message, status=n.status.value if hasattr(n.status, "value") else str(n.status)) for n in notifications]


@router.get("/{notification_id}", response_model=NotificationResponseSchema)
async def get_notification(notification_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_notification_repository(session)
    notification = await repo.find_by_id(notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificación no encontrada")
    check_ownership(notification, current_user)
    return NotificationResponseSchema(
        id=notification.id, user_id=notification.user_id, type=notification.type,
        title=notification.title, message=notification.message,
        status=notification.status.value if hasattr(notification.status, "value") else str(notification.status),
    )


@router.put("/{notification_id}", response_model=NotificationResponseSchema)
async def update_notification(notification_id: str, payload: UpdateNotificationRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_notification_repository(session)
    notification = await repo.find_by_id(notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificación no encontrada")
    check_ownership(notification, current_user)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(notification, field, value)

    await repo.save(notification)
    await session.commit()

    return NotificationResponseSchema(
        id=notification.id, user_id=notification.user_id, type=notification.type,
        title=notification.title, message=notification.message,
        status=notification.status.value if hasattr(notification.status, "value") else str(notification.status),
    )


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(notification_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_notification_repository(session)
    notification = await repo.find_by_id(notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificación no encontrada")
    check_ownership(notification, current_user)

    await repo.delete(notification_id)
    await session.commit()
