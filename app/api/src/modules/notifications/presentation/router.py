from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_notification_use_case, build_notification_repository
from infrastructure.database.session import get_session
from modules.notifications.presentation.schemas import CreateNotificationRequestSchema, NotificationResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("", response_model=NotificationResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_notification(payload: CreateNotificationRequestSchema, session: AsyncSession = Depends(get_session)):
    use_case = build_create_notification_use_case(session)
    try:
        input_dto = payload.to_input_dto()
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
async def list_notifications_by_user(user_id: str, session: AsyncSession = Depends(get_session)):
    repo = build_notification_repository(session)
    notifications = await repo.find_by_user(user_id)
    return [NotificationResponseSchema(id=n.id, user_id=n.user_id, type=n.type, title=n.title, message=n.message, status=n.status.value if hasattr(n.status, "value") else str(n.status)) for n in notifications]
