from __future__ import annotations

from dataclasses import dataclass

from modules.payment_methods.application.dtos import (
    GetPaymentMethodOutput,
    to_payment_method_output,
)
from modules.payment_methods.application.ports.payment_method_repository import (
    PaymentMethodRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class GetPaymentMethodInput:
    pm_id: str
    requester_id: str
    requester_role: str = "USER"


class GetPaymentMethodUseCase:
    def __init__(self, repo: PaymentMethodRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: GetPaymentMethodInput) -> GetPaymentMethodOutput:
        pm = await self._repo.find_by_id(inp.pm_id)

        if pm is None:
            raise NotFoundError(
                code="PM_NOT_FOUND",
                message="Método de pago no encontrado",
            )

        # Lectura: dueño o admin.
        if pm.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        return to_payment_method_output(pm)
