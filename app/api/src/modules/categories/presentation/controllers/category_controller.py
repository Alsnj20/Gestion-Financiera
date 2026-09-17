"""Category Controller — Orquesta use cases, maneja transacciones, traduce errores."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import NoReturn, TypeVar

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from modules.categories.application.ports.category_repository import (
    CategoryRepositoryPort,
)
from modules.categories.application.use_cases.archive_category import (
    ArchiveCategoryInput,
    ArchiveCategoryUseCase,
)
from modules.categories.application.use_cases.create_category import (
    CreateCategoryInput,
    CreateCategoryUseCase,
)
from modules.categories.application.use_cases.get_category import (
    GetCategoryInput,
    GetCategoryUseCase,
)
from modules.categories.application.use_cases.list_categories import (
    ListCategoriesInput,
    ListCategoriesUseCase,
)
from modules.categories.application.use_cases.restore_category import (
    RestoreCategoryInput,
    RestoreCategoryUseCase,
)
from modules.categories.application.use_cases.update_category import (
    UpdateCategoryInput,
    UpdateCategoryUseCase,
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


class CategoryController:
    """Recibe el port inyectado (testeable, sin acoplar presentation a infra)."""

    def __init__(self, repo: CategoryRepositoryPort, session: AsyncSession) -> None:
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

    async def create(self, inp: CreateCategoryInput) -> dict:
        result = await self._run_write(
            lambda: CreateCategoryUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def get(self, inp: GetCategoryInput) -> dict:
        result = await self._run_read(
            lambda: GetCategoryUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def list_by_user(self, inp: ListCategoriesInput) -> list[dict]:
        result = await self._run_read(
            lambda: ListCategoriesUseCase(self._repo).execute(inp)
        )
        return [asdict(item) for item in result]

    async def update(self, inp: UpdateCategoryInput) -> dict:
        result = await self._run_write(
            lambda: UpdateCategoryUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def archive(self, inp: ArchiveCategoryInput) -> None:
        await self._run_write(lambda: ArchiveCategoryUseCase(self._repo).execute(inp))

    async def restore(self, inp: RestoreCategoryInput) -> dict:
        result = await self._run_write(
            lambda: RestoreCategoryUseCase(self._repo).execute(inp)
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
