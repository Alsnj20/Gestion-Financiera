from __future__ import annotations

from dataclasses import dataclass

from modules.limits.application.dtos import ListLimitsOutput, to_limit_output
from modules.limits.application.ports.limit_repository import LimitRepositoryPort
from shared.errors import BusinessRuleError
from shared.types.enums import BudgetStatus


@dataclass(frozen=True, slots=True)
class ListLimitsInput:
    user_id: str
    requester_id: str
    requester_role: str = "USER"
    include_archived: bool = False


class ListLimitsUseCase:
    def __init__(self, repo: LimitRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: ListLimitsInput) -> list[ListLimitsOutput]:
        # Lectura: dueño o admin.
        if inp.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        limits = await self._repo.find_by_user(inp.user_id)
        if not inp.include_archived:
            limits = [l for l in limits if l.status == BudgetStatus.ACTIVE]
        return [to_limit_output(limit) for limit in limits]
