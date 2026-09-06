from __future__ import annotations

from dataclasses import dataclass
from modules.payment_methods.domain.entities.payment_method import PaymentMethod
from modules.payment_methods.application.ports.payment_method_repository import PaymentMethodRepositoryPort
from shared.errors import ConflictError


@dataclass(frozen=True, slots=True)
class CreatePaymentMethodInput:
    user_id: str
    account_id: str
    name: str
    type: str = ""
    is_default: bool = False


@dataclass(frozen=True, slots=True)
class CreatePaymentMethodOutput:
    id: str
    user_id: str
    account_id: str
    name: str
    type: str
    is_default: bool
    status: str


class CreatePaymentMethodUseCase:
    def __init__(self, repo: PaymentMethodRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: CreatePaymentMethodInput) -> CreatePaymentMethodOutput:
        if await self._repo.exists_name_for_user(inp.user_id, inp.name):
            raise ConflictError(code="PM_NAME_TAKEN", message=f"Método de pago ya existe: {inp.name}")

        pm = PaymentMethod.create(user_id=inp.user_id, account_id=inp.account_id, name=inp.name, type=inp.type, is_default=inp.is_default)
        await self._repo.save(pm)

        return CreatePaymentMethodOutput(
            id=pm.id, user_id=pm.user_id, account_id=pm.account_id, name=pm.name, type=pm.type,
            is_default=pm.is_default,
            status=pm.status.value if hasattr(pm.status, "value") else str(pm.status),
        )
