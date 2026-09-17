"""Notification Controller — Orquesta use cases, maneja transacciones, traduce errores."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import NoReturn, TypeVar

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from modules.notifications.application.ports.notification_repository import (
    NotificationRepositoryPort,
)
from modules.notifications.application.use_cases.cancel_notification import (
    CancelNotificationInput,
    CancelNotificationUseCase,
)
from modules.notifications.application.use_cases.create_notification import (
    CreateNotificationInput,
    CreateNotificationUseCase,
)
from modules.notifications.application.use_cases.delete_notification import (
    DeleteNotificationInput,
    DeleteNotificationUseCase,
)
from modules.notifications.application.use_cases.get_notification import (
    GetNotificationInput,
    GetNotificationUseCase,
)
from modules.notifications.application.use_cases.list_notifications import (
    ListNotificationsInput,
    ListNotificationsUseCase,
)
from modules.notifications.application.use_cases.send_notification import (
    SendNotificationInput,
    SendNotificationUseCase,
)
from modules.notifications.application.use_cases.update_notification import (
    UpdateNotificationInput,
    UpdateNotificationUseCase,
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


class NotificationController:
    """Recibe el port inyectado (testeable, sin acoplar presentation a infra)."""

    def __init__(self, repo: NotificationRepositoryPort, session: AsyncSession) -> None:
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

    async def create(self, inp: CreateNotificationInput) -> dict:
        result = await self._run_write(
            lambda: CreateNotificationUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def get(self, inp: GetNotificationInput) -> dict:
        result = await self._run_read(
            lambda: GetNotificationUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def list_by_user(self, inp: ListNotificationsInput) -> list[dict]:
        result = await self._run_read(
            lambda: ListNotificationsUseCase(self._repo).execute(inp)
        )
        return [asdict(item) for item in result]

    async def update(self, inp: UpdateNotificationInput) -> dict:
        result = await self._run_write(
            lambda: UpdateNotificationUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def send(self, inp: SendNotificationInput) -> dict:
        result = await self._run_write(
            lambda: SendNotificationUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def cancel(self, inp: CancelNotificationInput) -> dict:
        result = await self._run_write(
            lambda: CancelNotificationUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def delete(self, inp: DeleteNotificationInput) -> None:
        await self._run_write(
            lambda: DeleteNotificationUseCase(self._repo).execute(inp)
        )

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
