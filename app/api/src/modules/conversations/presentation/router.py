from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_conversation_message_use_case, build_conversation_message_repository
from modules.auth.presentation.dependencies import get_current_user, check_ownership
from infrastructure.database.session import get_session
from modules.conversations.presentation.schemas import CreateConversationMessageRequestSchema, ConversationMessageResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationMessageResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_conversation_message(payload: CreateConversationMessageRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    use_case = build_create_conversation_message_use_case(session)
    try:
        input_dto = payload.to_input_dto()
        input_dto.user_id = current_user["user_id"]
        result = await use_case.execute(input_dto)
        await session.commit()
        return ConversationMessageResponseSchema(
            id=result.id, user_id=result.user_id, channel=result.channel,
            external_message_id=result.external_message_id, direction=result.direction,
            content=result.content, parsed_intent=result.parsed_intent,
        )
    except (ValidationError, ValueError) as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "VALIDATION_ERROR", "message": str(e)}) from e
    except ConflictError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": e.code, "message": e.message}) from e


@router.get("/user/{user_id}", response_model=list[ConversationMessageResponseSchema])
async def list_conversation_messages_by_user(user_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    if user_id != current_user["user_id"] and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    repo = build_conversation_message_repository(session)
    items = await repo.find_by_user(user_id)
    return [
        ConversationMessageResponseSchema(
            id=m.id, user_id=m.user_id,
            channel=m.channel.value if hasattr(m.channel, "value") else str(m.channel),
            external_message_id=m.external_message_id,
            direction=m.direction.value if hasattr(m.direction, "value") else str(m.direction),
            content=m.content, parsed_intent=m.parsed_intent,
        )
        for m in items
    ]
