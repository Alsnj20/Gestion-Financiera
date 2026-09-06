"""DTOs de salida unificados del módulo accounts.

Antes existían 5 clases casi idénticas (Create/Update/Get/List/Restore)
con la inconsistencia de `Decimal` vs `str` en balances. Ahora hay una
sola fuente: `AccountOutput` (Decimal, verdad del dominio) + `to_account_output`.
Los nombres antiguos se conservan como alias para compatibilidad.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from modules.accounts.domain.entities.account import Account


@dataclass(frozen=True, slots=True)
class AccountOutput:
    id: str
    user_id: str
    name: str
    type: str
    currency: str
    initial_balance: Decimal
    current_balance: Decimal
    is_default: bool
    status: str


def to_account_output(account: Account) -> AccountOutput:
    return AccountOutput(
        id=account.id,
        user_id=account.user_id,
        name=account.name,
        type=account.type.value,
        currency=account.currency,
        initial_balance=account.initial_balance,
        current_balance=account.current_balance,
        is_default=account.is_default,
        status=account.status.value,
    )


# Aliases de compatibilidad (evitan romper imports existentes).
CreateAccountOutput = AccountOutput
UpdateAccountOutput = AccountOutput
GetAccountOutput = AccountOutput
ListAccountsByUserOutput = AccountOutput
RestoreAccountOutput = AccountOutput
