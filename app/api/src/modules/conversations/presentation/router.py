"""ConversationMessage Router — Solo enruta, delega al Controller (append-only)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from composition import get_conversation_message_controller
from modules.auth.presentation.dependencies import get_current_user
from modules.conversations.application.use_cases.list_conversation_messages import (
    ListConversationMessagesInput,
)
from modules.conversations.presentation.controllers.conversation_message_controller import (
    ConversationMessageController,
)
from modules.conversations.presentation.schemas import (
    ConversationMessageResponseSchema,
    CreateConversationMessageRequestSchema,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])

CurrentUser = Annotated[dict, Depends(get_current_user)]
ConversationMessageCtrl = Annotated[
    ConversationMessageController, Depends(get_conversation_message_controller)
]


@router.post(
    "",
    response_model=ConversationMessageResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation_message(
    payload: CreateConversationMessageRequestSchema,
    current_user: CurrentUser,
    controller: ConversationMessageCtrl,
):
    # user_id sale del JWT, nunca del body.
    result = await controller.create(
        payload.to_input_dto(user_id=current_user["user_id"])
    )
    return ConversationMessageResponseSchema(**result)


@router.get("/user/{user_id}", response_model=list[ConversationMessageResponseSchema])
async def list_conversation_messages_by_user(
    user_id: str,
    current_user: CurrentUser,
    controller: ConversationMessageCtrl,
):
    result = await controller.list_by_user(
        ListConversationMessagesInput(
            user_id=user_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return [ConversationMessageResponseSchema(**item) for item in result]
