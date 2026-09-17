"""ConversationMessage Controller — Orquesta use cases, traduce errores."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import NoReturn, TypeVar

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from modules.conversations.application.ports.conversation_message_repository import (
    ConversationMessageRepositoryPort,
)
from modules.conversations.application.use_cases.create_conversation_message import (
    CreateConversationMessageInput,
    CreateConversationMessageUseCase,
)
from modules.conversations.application.use_cases.list_conversation_messages import (
    ListConversationMessagesInput,
    ListConversationMessagesUseCase,
)
from shared.errors import (
    BusinessRuleError,
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)

T = TypeVar("T")

# Tabla única de traducción dominio -> HTTP.
_ERROR_HTTP_STATUS: dict[type[DomainError], int] = {
    ValidationError: 400,
    NotFoundError: 404,
    ConflictError: 409,
    BusinessRuleError: 403,
}


def _http_status_for(exc: DomainError) -> int:
    if isinstance(exc, BusinessRuleError) and exc.code != "FORBIDDEN":
        return 409
    return _ERROR_HTTP_STATUS.get(type(exc), 500)


class ConversationMessageController:
    """Append-only: solo crear y listar."""

    def __init__(
        self, repo: ConversationMessageRepositoryPort, session: AsyncSession
    ) -> None:
        self._repo = repo
        self._session = session

    async def _run_read(self, fn: Callable[[], Awaitable[T]]) -> T:
        try:
            return await fn()
        except DomainError as exc:
            self._raise(_http_status_for(exc), exc.code, exc.message)

    async def _run_write(self, fn: Callable[[], Awaitable[T]]) -> T:
        try:
            result = await fn()
            await self._session.commit()
            return result
        except DomainError as exc:
            await self._session.rollback()
            self._raise(_http_status_for(exc), exc.code, exc.message)

    async def create(self, inp: CreateConversationMessageInput) -> dict:
        result = await self._run_write(
            lambda: CreateConversationMessageUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def list_by_user(self, inp: ListConversationMessagesInput) -> list[dict]:
        result = await self._run_read(
            lambda: ListConversationMessagesUseCase(self._repo).execute(inp)
        )
        return [asdict(item) for item in result]

    @staticmethod
    def _raise(
        status_code: int,
        error_code: str,
        message: str,
    ) -> NoReturn:
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": error_code,
                "message": message,
            },
        )
