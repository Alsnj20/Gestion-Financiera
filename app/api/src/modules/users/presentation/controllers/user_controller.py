"""User Controller — Orquesta use cases, maneja transacciones, traduce errores."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import NoReturn, TypeVar

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from modules.users.application.ports.user_repository import UserRepositoryPort
from modules.users.application.use_cases.delete_user import (
    DeleteUserInput,
    DeleteUserUseCase,
)
from modules.users.application.use_cases.get_user import GetUserInput, GetUserUseCase
from modules.users.application.use_cases.list_users import (
    ListUsersInput,
    ListUsersUseCase,
)
from modules.users.application.use_cases.update_user import (
    UpdateUserInput,
    UpdateUserUseCase,
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


class UserController:
    """Recibe el port inyectado (testeable, sin acoplar presentation a infra)."""

    def __init__(self, repo: UserRepositoryPort, session: AsyncSession) -> None:
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

    async def get(self, inp: GetUserInput) -> dict:
        result = await self._run_read(lambda: GetUserUseCase(self._repo).execute(inp))
        return asdict(result)

    async def list_all(self, inp: ListUsersInput) -> list[dict]:
        result = await self._run_read(lambda: ListUsersUseCase(self._repo).execute(inp))
        return [asdict(item) for item in result]

    async def update(self, inp: UpdateUserInput) -> dict:
        result = await self._run_write(
            lambda: UpdateUserUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def delete(self, inp: DeleteUserInput) -> None:
        await self._run_write(lambda: DeleteUserUseCase(self._repo).execute(inp))

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
