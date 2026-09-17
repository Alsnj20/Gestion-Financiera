from __future__ import annotations

from dataclasses import dataclass

from modules.payment_methods.application.dtos import (
    ListPaymentMethodsOutput,
    to_payment_method_output,
)
from modules.payment_methods.application.ports.payment_method_repository import (
    PaymentMethodRepositoryPort,
)
from shared.errors import BusinessRuleError


@dataclass(frozen=True, slots=True)
class ListPaymentMethodsInput:
    user_id: str
    requester_id: str
    requester_role: str = "USER"


class ListPaymentMethodsUseCase:
    def __init__(self, repo: PaymentMethodRepositoryPort) -> None:
        self._repo = repo

    async def execute(
        self, inp: ListPaymentMethodsInput
    ) -> list[ListPaymentMethodsOutput]:
        # Lectura: dueño o admin.
        if inp.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        methods = await self._repo.find_by_user(inp.user_id)
        return [to_payment_method_output(pm) for pm in methods]
