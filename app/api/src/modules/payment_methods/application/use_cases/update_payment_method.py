from __future__ import annotations

from dataclasses import dataclass

from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from modules.payment_methods.application.dtos import (
    UpdatePaymentMethodOutput,
    to_payment_method_output,
)
from modules.payment_methods.application.ports.payment_method_repository import (
    PaymentMethodRepositoryPort,
)
from modules.payment_methods.application.use_cases.create_payment_method import (
    _resolve_account,
)
from shared.errors import BusinessRuleError, ConflictError, NotFoundError


@dataclass(frozen=True, slots=True)
class UpdatePaymentMethodInput:
    pm_id: str
    user_id: str
    name: str | None = None
    type: str | None = None
    account_id: str | None = None
    is_default: bool | None = None


class UpdatePaymentMethodUseCase:
    def __init__(
        self, repo: PaymentMethodRepositoryPort, account_repo: AccountRepositoryPort
    ) -> None:
        self._repo = repo
        self._account_repo = account_repo

    async def execute(self, inp: UpdatePaymentMethodInput) -> UpdatePaymentMethodOutput:
        pm = await self._repo.find_by_id(inp.pm_id)

        if pm is None:
            raise NotFoundError(
                code="PM_NOT_FOUND",
                message="Método de pago no encontrado",
            )

        # Escritura: solo el dueño (admin solo lee el ledger ajeno).
        if pm.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )
        if pm.is_archived():
            raise BusinessRuleError(
                code="PM_ARCHIVED",
                message="Método archivado no se puede editar. Restaúralo primero.",
            )

        if inp.account_id is not None and inp.account_id != pm.account_id:
            pm = pm.change_account(
                await _resolve_account(self._account_repo, inp.user_id, inp.account_id)
            )

        if inp.name is not None and inp.name != pm.name:
            if await self._repo.exists_name_for_user(inp.user_id, inp.name):
                raise ConflictError(
                    code="PM_NAME_TAKEN",
                    message=f"Nombre ya existe: {inp.name}",
                )
            pm = pm.rename(inp.name)

        if inp.type is not None:
            pm = pm.change_type(inp.type)

        if inp.is_default is True:
            await self._repo.clear_default_for_user(inp.user_id)
            pm = pm.mark_as_default()
        elif inp.is_default is False:
            pm = pm.unmark_as_default()

        await self._repo.save(pm)

        return to_payment_method_output(pm)
