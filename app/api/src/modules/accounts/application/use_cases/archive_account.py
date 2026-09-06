from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from modules.accounts.application.ports.account_repository import (
    AccountRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError
from shared.types.enums import AccountStatus


@dataclass(frozen=True, slots=True)
class ArchiveAccountInput:
    account_id: str
    user_id: str


class ArchiveAccountUseCase:
    def __init__(self, account_repo: AccountRepositoryPort) -> None:
        self._account_repo = account_repo

    async def execute(self, inp: ArchiveAccountInput) -> None:
        account = await self._account_repo.find_by_id(inp.account_id)

        if account is None:
            raise NotFoundError(
                code="ACCOUNT_NOT_FOUND",
                message="Cuenta no encontrada",
            )

        # Solo el dueño archiva (ni siquiera admin edita).
        if account.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        # Idempotente: ya archivada no hace nada.
        if account.status == AccountStatus.ARCHIVED:
            return

        # No archivar la última cuenta activa.
        actives = [
            a
            for a in await self._account_repo.find_by_user(inp.user_id)
            if a.status == AccountStatus.ACTIVE
        ]
        if len(actives) <= 1:
            raise BusinessRuleError(
                code="ACCOUNT_LAST_ACTIVE",
                message="No se puede archivar la última cuenta activa.",
            )

        # No archivar con saldo distinto de cero.
        if account.current_balance != Decimal("0.00"):
            raise BusinessRuleError(
                code="ACCOUNT_HAS_BALANCE",
                message="Transfiere el saldo a otra cuenta antes de archivarla.",
            )

        # archive_with_shadow_name ya desmarca is_default y renombra.
        await self._account_repo.save(account.archive_with_shadow_name())
