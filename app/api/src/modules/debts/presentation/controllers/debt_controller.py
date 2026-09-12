"""Debt Controller — Orquesta use cases, maneja transacciones, traduce errores."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import NoReturn, TypeVar

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from modules.debts.application.ports.debt_repository import DebtRepositoryPort
from modules.debts.application.use_cases.cancel_debt import (
    CancelDebtInput,
    CancelDebtUseCase,
)
from modules.debts.application.use_cases.create_debt import (
    CreateDebtInput,
    CreateDebtUseCase,
)
from modules.debts.application.use_cases.get_debt import GetDebtInput, GetDebtUseCase
from modules.debts.application.use_cases.list_debts import (
    ListDebtsInput,
    ListDebtsUseCase,
)
from modules.debts.application.use_cases.register_debt_payment import (
    RegisterDebtPaymentInput,
    RegisterDebtPaymentUseCase,
)
from modules.debts.application.use_cases.update_debt import (
    UpdateDebtInput,
    UpdateDebtUseCase,
)
from modules.transactions.application.ports.transaction_repository import (
    TransactionRepositoryPort,
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


class DebtController:
    """Recibe el port inyectado (testeable, sin acoplar presentation a infra)."""

    def __init__(
        self,
        repo: DebtRepositoryPort,
        tx_repo: TransactionRepositoryPort,
        account_repo: AccountRepositoryPort,
        session: AsyncSession,
    ) -> None:
        self._repo = repo
        self._tx_repo = tx_repo
        self._account_repo = account_repo
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

    async def create(self, inp: CreateDebtInput) -> dict:
        result = await self._run_write(
            lambda: CreateDebtUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def get(self, inp: GetDebtInput) -> dict:
        result = await self._run_read(lambda: GetDebtUseCase(self._repo).execute(inp))
        return asdict(result)

    async def list_by_user(self, inp: ListDebtsInput) -> list[dict]:
        result = await self._run_read(lambda: ListDebtsUseCase(self._repo).execute(inp))
        return [asdict(item) for item in result]

    async def update(self, inp: UpdateDebtInput) -> dict:
        result = await self._run_write(
            lambda: UpdateDebtUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def cancel(self, inp: CancelDebtInput) -> dict:
        result = await self._run_write(
            lambda: CancelDebtUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def register_payment(self, inp: RegisterDebtPaymentInput) -> dict:
        result = await self._run_write(
            lambda: RegisterDebtPaymentUseCase(
                self._repo, self._tx_repo, self._account_repo
            ).execute(inp)
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
