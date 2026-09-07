"""Transfer Controller — Orquesta use cases, maneja transacciones, traduce errores."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import NoReturn, TypeVar

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from modules.transactions.application.ports.transaction_repository import (
    TransactionRepositoryPort,
)
from modules.transfers.application.ports.transfer_repository import (
    TransferRepositoryPort,
)
from modules.transfers.application.use_cases.create_transfer import (
    CreateTransferInput,
    CreateTransferUseCase,
)
from modules.transfers.application.use_cases.get_transfer import (
    GetTransferInput,
    GetTransferUseCase,
)
from modules.transfers.application.use_cases.reverse_transfer import (
    ReverseTransferInput,
    ReverseTransferUseCase,
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


class TransferController:
    """Recibe los ports inyectados (testeable, sin acoplar presentation a infra)."""

    def __init__(
        self,
        transfer_repo: TransferRepositoryPort,
        tx_repo: TransactionRepositoryPort,
        account_repo: AccountRepositoryPort,
        session: AsyncSession,
    ) -> None:
        self._transfer_repo = transfer_repo
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

    async def create(self, inp: CreateTransferInput) -> dict:
        result = await self._run_write(
            lambda: CreateTransferUseCase(
                self._transfer_repo, self._tx_repo, self._account_repo
            ).execute(inp)
        )
        return asdict(result)

    async def get(self, inp: GetTransferInput) -> dict:
        result = await self._run_read(
            lambda: GetTransferUseCase(self._transfer_repo).execute(inp)
        )
        return asdict(result)

    async def reverse(self, inp: ReverseTransferInput) -> dict:
        result = await self._run_write(
            lambda: ReverseTransferUseCase(
                self._transfer_repo, self._tx_repo, self._account_repo
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
