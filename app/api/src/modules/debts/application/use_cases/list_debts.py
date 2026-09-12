from __future__ import annotations

from dataclasses import dataclass

from modules.debts.application.dtos import ListDebtsOutput, to_debt_output
from modules.debts.application.ports.debt_repository import DebtRepositoryPort
from shared.errors import BusinessRuleError


@dataclass(frozen=True, slots=True)
class ListDebtsInput:
    user_id: str
    requester_id: str
    requester_role: str = "USER"


class ListDebtsUseCase:
    def __init__(self, repo: DebtRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: ListDebtsInput) -> list[ListDebtsOutput]:
        # Lectura: dueño o admin.
        if inp.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        debts = await self._repo.find_by_user(inp.user_id)
        return [
            to_debt_output(
                debt,
                await self._repo.list_installments(debt.id),
                await self._repo.list_payments(debt.id),
            )
            for debt in debts
        ]
