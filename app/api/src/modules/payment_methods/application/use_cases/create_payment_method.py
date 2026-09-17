from __future__ import annotations

from dataclasses import dataclass

from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from modules.payment_methods.application.dtos import (
    CreatePaymentMethodOutput,
    to_payment_method_output,
)
from modules.payment_methods.application.ports.payment_method_repository import (
    PaymentMethodRepositoryPort,
)
from modules.payment_methods.domain.entities.payment_method import PaymentMethod
from shared.errors import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from shared.types.enums import AccountStatus


@dataclass(frozen=True, slots=True)
class CreatePaymentMethodInput:
    user_id: str
    account_id: str
    name: str
    type: str = ""
    is_default: bool = False


async def _resolve_account(
    account_repo: AccountRepositoryPort, user_id: str, account_id: str
) -> str:
    """La cuenta debe existir y ser del usuario (método con causa)."""
    account = await account_repo.find_by_id(account_id)
    if account is None:
        raise NotFoundError(
            code="PM_ACCOUNT_NOT_FOUND",
            message="Cuenta no encontrada",
        )
    if account.user_id != user_id:
        raise BusinessRuleError(
            code="FORBIDDEN",
            message="No autorizado",
        )
    if account.status == AccountStatus.ARCHIVED:
        raise BusinessRuleError(
            code="PM_ACCOUNT_ARCHIVED",
            message="La cuenta está archivada.",
        )
    return account.id


class CreatePaymentMethodUseCase:
    def __init__(
        self, repo: PaymentMethodRepositoryPort, account_repo: AccountRepositoryPort
    ) -> None:
        self._repo = repo
        self._account_repo = account_repo

    async def execute(self, inp: CreatePaymentMethodInput) -> CreatePaymentMethodOutput:
        if not inp.account_id:
            raise ValidationError(
                code="PM_ACCOUNT_REQUIRED", message="account_id requerido"
            )

        account_id = await _resolve_account(
            self._account_repo, inp.user_id, inp.account_id
        )

        if await self._repo.exists_name_for_user(inp.user_id, inp.name):
            raise ConflictError(
                code="PM_NAME_TAKEN", message=f"Método de pago ya existe: {inp.name}"
            )

        if inp.is_default:
            await self._repo.clear_default_for_user(inp.user_id)

        pm = PaymentMethod.create(
            user_id=inp.user_id,
            account_id=account_id,
            name=inp.name,
            type=inp.type,
            is_default=inp.is_default,
        )
        await self._repo.save(pm)

        return to_payment_method_output(pm)
