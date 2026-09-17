from __future__ import annotations

from dataclasses import dataclass

from modules.payment_methods.application.dtos import (
    RestorePaymentMethodOutput,
    to_payment_method_output,
)
from modules.payment_methods.application.ports.payment_method_repository import (
    PaymentMethodRepositoryPort,
)
from shared.domain.guards import shadow_original_name
from shared.errors import BusinessRuleError, ConflictError, NotFoundError


@dataclass(frozen=True, slots=True)
class RestorePaymentMethodInput:
    pm_id: str
    user_id: str


class RestorePaymentMethodUseCase:
    def __init__(self, repo: PaymentMethodRepositoryPort) -> None:
        self._repo = repo

    async def execute(
        self, inp: RestorePaymentMethodInput
    ) -> RestorePaymentMethodOutput:
        pm = await self._repo.find_by_id(inp.pm_id, for_update=True)

        if pm is None:
            raise NotFoundError(
                code="PM_NOT_FOUND",
                message="Método de pago no encontrado",
            )

        # Solo el dueño restaura.
        if pm.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        if not pm.is_archived():
            raise BusinessRuleError(
                code="PM_NOT_ARCHIVED",
                message="Solo se puede restaurar un método archivado.",
            )

        original = shadow_original_name(pm.name)
        if await self._repo.exists_name_for_user(inp.user_id, original):
            raise ConflictError(
                code="PM_NAME_TAKEN",
                message=f"Ya existe un método con el nombre: {original}",
            )

        restored = pm.restore(original)
        await self._repo.save(restored)

        return to_payment_method_output(restored)
