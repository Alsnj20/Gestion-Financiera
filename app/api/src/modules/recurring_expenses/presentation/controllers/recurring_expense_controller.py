"""RecurringExpense Controller — Orquesta use cases, maneja transacciones, traduce errores."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import NoReturn, TypeVar

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from modules.categories.application.ports.category_repository import (
    CategoryRepositoryPort,
)
from modules.recurring_expenses.application.ports.recurring_expense_repository import (
    RecurringExpenseRepositoryPort,
)
from modules.recurring_expenses.application.use_cases.cancel_recurring_expense import (
    CancelRecurringExpenseInput,
    CancelRecurringExpenseUseCase,
)
from modules.recurring_expenses.application.use_cases.create_recurring_expense import (
    CreateRecurringExpenseInput,
    CreateRecurringExpenseUseCase,
)
from modules.recurring_expenses.application.use_cases.get_recurring_expense import (
    GetRecurringExpenseInput,
    GetRecurringExpenseUseCase,
)
from modules.recurring_expenses.application.use_cases.list_recurring_expenses import (
    ListRecurringExpensesInput,
    ListRecurringExpensesUseCase,
)
from modules.recurring_expenses.application.use_cases.pause_recurring_expense import (
    PauseRecurringExpenseInput,
    PauseRecurringExpenseUseCase,
)
from modules.recurring_expenses.application.use_cases.resume_recurring_expense import (
    ResumeRecurringExpenseInput,
    ResumeRecurringExpenseUseCase,
)
from modules.recurring_expenses.application.use_cases.update_recurring_expense import (
    UpdateRecurringExpenseInput,
    UpdateRecurringExpenseUseCase,
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


class RecurringExpenseController:
    """Recibe los ports inyectados (testeable, sin acoplar presentation a infra)."""

    def __init__(
        self,
        repo: RecurringExpenseRepositoryPort,
        account_repo: AccountRepositoryPort,
        category_repo: CategoryRepositoryPort,
        session: AsyncSession,
    ) -> None:
        self._repo = repo
        self._account_repo = account_repo
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

    async def create(self, inp: CreateRecurringExpenseInput) -> dict:
        result = await self._run_write(
            lambda: CreateRecurringExpenseUseCase(
                self._repo, self._account_repo, self._category_repo
            ).execute(inp)
        )
        return asdict(result)

    async def get(self, inp: GetRecurringExpenseInput) -> dict:
        result = await self._run_read(
            lambda: GetRecurringExpenseUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def list_by_user(self, inp: ListRecurringExpensesInput) -> list[dict]:
        result = await self._run_read(
            lambda: ListRecurringExpensesUseCase(self._repo).execute(inp)
        )
        return [asdict(item) for item in result]

    async def update(self, inp: UpdateRecurringExpenseInput) -> dict:
        result = await self._run_write(
            lambda: UpdateRecurringExpenseUseCase(
                self._repo, self._category_repo
            ).execute(inp)
        )
        return asdict(result)

    async def pause(self, inp: PauseRecurringExpenseInput) -> dict:
        result = await self._run_write(
            lambda: PauseRecurringExpenseUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def resume(self, inp: ResumeRecurringExpenseInput) -> dict:
        result = await self._run_write(
            lambda: ResumeRecurringExpenseUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def cancel(self, inp: CancelRecurringExpenseInput) -> dict:
        result = await self._run_write(
            lambda: CancelRecurringExpenseUseCase(self._repo).execute(inp)
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
