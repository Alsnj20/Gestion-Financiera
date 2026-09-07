from __future__ import annotations

from datetime import datetime
from typing import Protocol

from modules.transactions.domain.entities.transaction import Transaction


class TransactionRepositoryPort(Protocol):
    """Sin borrado físico: el libro mayor no se reescribe.

    Anular = cancelar (status CANCELLED) revirtiendo el balance.
    Además loan/debt_payments y transfers referencian con RESTRICT.
    """

    async def save(self, tx: Transaction) -> None: ...
    async def find_by_id(
        self, tx_id: str, *, for_update: bool = False
    ) -> Transaction | None: ...
    async def list_by_user(
        self,
        user_id: str,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        account_id: str | None = None,
        type: str | None = None,
    ) -> list[Transaction]: ...
