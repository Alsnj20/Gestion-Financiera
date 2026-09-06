from __future__ import annotations

from typing import Protocol
from modules.debts.domain.entities.debt import Debt


class DebtRepositoryPort(Protocol):
    async def save(self, debt: Debt) -> None: ...
    async def find_by_id(self, debt_id: str) -> Debt | None: ...
    async def find_by_user(self, user_id: str) -> list[Debt]: ...
