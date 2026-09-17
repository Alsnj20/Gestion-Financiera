"""PaymentMethod Controller — Orquesta use cases, maneja transacciones, traduce errores."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import NoReturn, TypeVar

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from modules.payment_methods.application.ports.payment_method_repository import (
    PaymentMethodRepositoryPort,
)
from modules.payment_methods.application.use_cases.archive_payment_method import (
    ArchivePaymentMethodInput,
    ArchivePaymentMethodUseCase,
)
from modules.payment_methods.application.use_cases.create_payment_method import (
    CreatePaymentMethodInput,
    CreatePaymentMethodUseCase,
)
from modules.payment_methods.application.use_cases.get_payment_method import (
    GetPaymentMethodInput,
    GetPaymentMethodUseCase,
)
from modules.payment_methods.application.use_cases.list_payment_methods import (
    ListPaymentMethodsInput,
    ListPaymentMethodsUseCase,
)
from modules.payment_methods.application.use_cases.restore_payment_method import (
    RestorePaymentMethodInput,
    RestorePaymentMethodUseCase,
)
from modules.payment_methods.application.use_cases.update_payment_method import (
    UpdatePaymentMethodInput,
    UpdatePaymentMethodUseCase,
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


class PaymentMethodController:
    """Recibe los ports inyectados (testeable, sin acoplar presentation a infra)."""

    def __init__(
        self,
        repo: PaymentMethodRepositoryPort,
        account_repo: AccountRepositoryPort,
        session: AsyncSession,
    ) -> None:
        self._repo = repo
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

    async def create(self, inp: CreatePaymentMethodInput) -> dict:
        result = await self._run_write(
            lambda: CreatePaymentMethodUseCase(self._repo, self._account_repo).execute(
                inp
            )
        )
        return asdict(result)

    async def get(self, inp: GetPaymentMethodInput) -> dict:
        result = await self._run_read(
            lambda: GetPaymentMethodUseCase(self._repo).execute(inp)
        )
        return asdict(result)

    async def list_by_user(self, inp: ListPaymentMethodsInput) -> list[dict]:
        result = await self._run_read(
            lambda: ListPaymentMethodsUseCase(self._repo).execute(inp)
        )
        return [asdict(item) for item in result]

    async def update(self, inp: UpdatePaymentMethodInput) -> dict:
        result = await self._run_write(
            lambda: UpdatePaymentMethodUseCase(self._repo, self._account_repo).execute(
                inp
            )
        )
        return asdict(result)

    async def archive(self, inp: ArchivePaymentMethodInput) -> None:
        await self._run_write(
            lambda: ArchivePaymentMethodUseCase(self._repo).execute(inp)
        )

    async def restore(self, inp: RestorePaymentMethodInput) -> dict:
        result = await self._run_write(
            lambda: RestorePaymentMethodUseCase(self._repo).execute(inp)
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
