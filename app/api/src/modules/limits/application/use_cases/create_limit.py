from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from modules.limits.domain.entities.limit import Limit
from modules.limits.application.ports.limit_repository import LimitRepositoryPort


@dataclass(frozen=True, slots=True)
class CreateLimitInput:
    user_id: str
    name: str
    amount: Decimal
    period_type: str = "MONTHLY"
    category_id: str = ""
    threshold_warning: Decimal = Decimal("80")


@dataclass(frozen=True, slots=True)
class CreateLimitOutput:
    id: str
    user_id: str
    name: str
    amount: Decimal
    period_type: str
    category_id: str
    threshold_warning: Decimal
    status: str


class CreateLimitUseCase:
    def __init__(self, repo: LimitRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: CreateLimitInput) -> CreateLimitOutput:
        limit = Limit.create(
            user_id=inp.user_id, name=inp.name, amount=inp.amount,
            period_type=inp.period_type, category_id=inp.category_id, threshold_warning=inp.threshold_warning,
        )
        await self._repo.save(limit)

        return CreateLimitOutput(
            id=limit.id, user_id=limit.user_id, name=limit.name, amount=limit.amount,
            period_type=limit.period_type.value if hasattr(limit.period_type, "value") else str(limit.period_type),
            category_id=limit.category_id, threshold_warning=limit.threshold_warning,
            status=limit.status.value if hasattr(limit.status, "value") else str(limit.status),
        )
