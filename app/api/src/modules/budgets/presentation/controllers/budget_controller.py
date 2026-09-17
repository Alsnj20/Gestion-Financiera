"""Budget Controller — Orquesta use cases, maneja transacciones, traduce errores."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import NoReturn, TypeVar

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from modules.budgets.application.ports.budget_repository import BudgetRepositoryPort
from modules.budgets.application.use_cases.archive_budget import (
    ArchiveBudgetInput,
    ArchiveBudgetUseCase,
)
from modules.budgets.application.use_cases.create_budget import (
    CreateBudgetInput,
    CreateBudgetUseCase,
)
from modules.budgets.application.use_cases.get_budget import (
    GetBudgetInput,
    GetBudgetUseCase,
)
from modules.budgets.application.use_cases.list_budgets import (
    ListBudgetsInput,
    ListBudgetsUseCase,
)
from modules.budgets.application.use_cases.restore_budget import (
    RestoreBudgetInput,
    RestoreBudgetUseCase,
)
from modules.budgets.application.use_cases.update_budget import (
    UpdateBudgetInput,
    UpdateBudgetUseCase,
)
from modules.categories.application.ports.category_repository import (
    CategoryRepositoryPort,
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


class BudgetController:
    """Recibe los ports inyectados (testeable, sin acoplar presentation a infra)."""

    def __init__(
        self,
        repo: BudgetRepositoryPort,
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

    async def create(self, inp: CreateBudgetInput) -> dict:
        result = await self._run_write(
            lambda: CreateBudgetUseCase(self._repo, self._category_repo).execute(inp)
        )
        return asdict(result)

    async def get(self, inp: GetBudgetInput) -> dict:
        result = await self._run_read(lambda: GetBudgetUseCase(self._repo).execute(inp))
        return asdict(result)

    async def list_by_user(self, inp: ListBudgetsInput) -> list[dict]:
        result = await self._run_read(
            lambda: ListBudgetsUseCase(self._repo).execute(inp)
        )
        return [asdict(item) for item in result]

    async def update(self, inp: UpdateBudgetInput) -> dict:
        result = await self._run_write(
            lambda: UpdateBudgetUseCase(self._repo, self._category_repo).execute(inp)
        )
        return asdict(result)

    async def archive(self, inp: ArchiveBudgetInput) -> None:
        await self._run_write(lambda: ArchiveBudgetUseCase(self._repo).execute(inp))

    async def restore(self, inp: RestoreBudgetInput) -> dict:
        result = await self._run_write(
            lambda: RestoreBudgetUseCase(self._repo).execute(inp)
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
