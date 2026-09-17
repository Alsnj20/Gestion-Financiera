"""Limit Controller — Orquesta use cases, maneja transacciones, traduce errores."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import NoReturn, TypeVar

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from modules.categories.application.ports.category_repository import (
    CategoryRepositoryPort,
)
from modules.limits.application.ports.limit_repository import LimitRepositoryPort
from modules.limits.application.use_cases.archive_limit import (
    ArchiveLimitInput,
    ArchiveLimitUseCase,
)
from modules.limits.application.use_cases.create_limit import (
    CreateLimitInput,
    CreateLimitUseCase,
)
from modules.limits.application.use_cases.get_limit import (
    GetLimitInput,
    GetLimitUseCase,
)
from modules.limits.application.use_cases.list_limits import (
    ListLimitsInput,
    ListLimitsUseCase,
)
from modules.limits.application.use_cases.restore_limit import (
    RestoreLimitInput,
    RestoreLimitUseCase,
)
from modules.limits.application.use_cases.update_limit import (
    UpdateLimitInput,
    UpdateLimitUseCase,
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


class LimitController:
    """Recibe los ports inyectados (testeable, sin acoplar presentation a infra)."""

    def __init__(
        self,
        repo: LimitRepositoryPort,
        category_repo: CategoryRepositoryPort,
        session: AsyncSession,
    ) -> None:
        self._repo = repo
        self._category_repo = category_repo
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

    async def create(self, inp: CreateLimitInput) -> dict:
        result = await self._run_write(
            lambda: CreateLimitUseCase(self._repo, self._category_repo).execute(inp)
        )
        return asdict(result)

    async def get(self, inp: GetLimitInput) -> dict:
        result = await self._run_read(lambda: GetLimitUseCase(self._repo).execute(inp))
        return asdict(result)

    async def list_by_user(self, inp: ListLimitsInput) -> list[dict]:
        result = await self._run_read(
            lambda: ListLimitsUseCase(self._repo).execute(inp)
        )
        return [asdict(item) for item in result]

    async def update(self, inp: UpdateLimitInput) -> dict:
        result = await self._run_write(
            lambda: UpdateLimitUseCase(self._repo, self._category_repo).execute(inp)
        )
        return asdict(result)

    async def archive(self, inp: ArchiveLimitInput) -> None:
        await self._run_write(lambda: ArchiveLimitUseCase(self._repo).execute(inp))

    async def restore(self, inp: RestoreLimitInput) -> dict:
        result = await self._run_write(
            lambda: RestoreLimitUseCase(self._repo).execute(inp)
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
