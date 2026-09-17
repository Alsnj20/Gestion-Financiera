from __future__ import annotations

from typing import Protocol

from modules.budgets.domain.entities.budget import Budget


class BudgetRepositoryPort(Protocol):
    """Sin borrado físico: anular = archivar (status ARCHIVED)."""

    async def save(self, budget: Budget) -> None: ...
    async def find_by_id(
        self, budget_id: str, *, for_update: bool = False
    ) -> Budget | None: ...
    async def find_by_user(self, user_id: str) -> list[Budget]: ...
