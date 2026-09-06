"""Account Controller — Orquesta use cases, maneja transacciones, traduce errores."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import NoReturn, TypeVar

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from modules.accounts.application.use_cases.archive_account import (
    ArchiveAccountInput,
    ArchiveAccountUseCase,
)
from modules.accounts.application.use_cases.create_account import (
    CreateAccountInput,
    CreateAccountUseCase,
)
from modules.accounts.application.use_cases.get_account import (
    GetAccountInput,
    GetAccountUseCase,
)
from modules.accounts.application.use_cases.list_accounts import (
    ListAccountsByUserInput,
    ListAccountsByUserUseCase,
)
from modules.accounts.application.use_cases.restore_account import (
    RestoreAccountInput,
    RestoreAccountUseCase,
)
from modules.accounts.application.use_cases.update_account import (
    UpdateAccountInput,
    UpdateAccountUseCase,
)
from shared.errors import (
    BusinessRuleError,
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)

T = TypeVar("T")

# Tabla única de traducción dominio -> HTTP (elimina 6 bloques try/except).
_ERROR_HTTP_STATUS: dict[type[DomainError], int] = {
    ValidationError: 400,
    NotFoundError: 404,
    ConflictError: 409,
    BusinessRuleError: 403,
}


def _http_status_for(exc: DomainError) -> int:
    """FORBIDDEN -> 403, resto de BusinessRule -> 409 (archive/restore)."""
    if isinstance(exc, BusinessRuleError) and exc.code != "FORBIDDEN":
        return 409
    return _ERROR_HTTP_STATUS.get(type(exc), 500)


class AccountController:
    """Recibe el port inyectado (testeable, sin acoplar presentation a infra)."""

    def __init__(self, repo: AccountRepositoryPort, session: AsyncSession) -> None:
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

    async def create(self, inp: CreateAccountInput) -> dict:
        result = await self._run_write(
            lambda: CreateAccountUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def get(self, inp: GetAccountInput) -> dict:
        result = await self._run_read(
            lambda: GetAccountUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def list_by_user(self, inp: ListAccountsByUserInput) -> list[dict]:
        result = await self._run_read(
            lambda: ListAccountsByUserUseCase(self._repo).execute(inp)
        )
        return [asdict(item) for item in result]

    async def update(
        self,
        inp: UpdateAccountInput,
    ) -> dict:
        result = await self._run_write(
            lambda: UpdateAccountUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def archive(self, inp: ArchiveAccountInput) -> None:
        await self._run_write(lambda: ArchiveAccountUseCase(self._repo).execute(inp))

    async def restore(self, inp: RestoreAccountInput) -> dict:
        result = await self._run_write(
            lambda: RestoreAccountUseCase(self._repo).execute(inp)
        )
        return asdict(result)

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
