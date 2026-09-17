from __future__ import annotations

from dataclasses import dataclass

from modules.payment_methods.application.ports.payment_method_repository import (
    PaymentMethodRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class ArchivePaymentMethodInput:
    pm_id: str
    user_id: str


class ArchivePaymentMethodUseCase:
    def __init__(self, repo: PaymentMethodRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: ArchivePaymentMethodInput) -> None:
        pm = await self._repo.find_by_id(inp.pm_id, for_update=True)

        if pm is None:
            raise NotFoundError(
                code="PM_NOT_FOUND",
                message="Método de pago no encontrado",
            )

        # Solo el dueño archiva.
        if pm.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        # Idempotente: ya archivado no hace nada.
        if pm.is_archived():
            return

        # archive_with_shadow_name libera el nombre original.
        await self._repo.save(pm.archive_with_shadow_name())
