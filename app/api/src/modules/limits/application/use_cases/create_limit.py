from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from modules.categories.application.ports.category_repository import (
    CategoryRepositoryPort,
)
from modules.limits.application.dtos import CreateLimitOutput, to_limit_output
from modules.limits.application.ports.limit_repository import LimitRepositoryPort
from modules.limits.domain.entities.limit import Limit
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class CreateLimitInput:
    user_id: str
    name: str
    amount: Decimal
    period_type: str = "MONTHLY"
    category_id: str = ""
    threshold_warning: Decimal = Decimal(80)


async def _resolve_category(
    category_repo: CategoryRepositoryPort, user_id: str, category_id: str
) -> str:
    """La categoría debe existir y ser del usuario (límite con causa)."""
    if not category_id:
        return ""
    category = await category_repo.find_by_id(category_id)
    if category is None:
        raise NotFoundError(
            code="LIMIT_CATEGORY_NOT_FOUND",
            message="Categoría no encontrada",
        )
    if category.user_id != user_id:
        raise BusinessRuleError(
            code="FORBIDDEN",
            message="No autorizado",
        )
    if category.is_archived():
        raise BusinessRuleError(
            code="LIMIT_CATEGORY_ARCHIVED",
            message="La categoría está archivada.",
        )
    return category.id


class CreateLimitUseCase:
    def __init__(
        self, repo: LimitRepositoryPort, category_repo: CategoryRepositoryPort
    ) -> None:
        self._repo = repo
        self._category_repo = category_repo

    async def execute(self, inp: CreateLimitInput) -> CreateLimitOutput:
        category_id = await _resolve_category(
            self._category_repo, inp.user_id, inp.category_id
        )

        limit = Limit.create(
            user_id=inp.user_id,
            name=inp.name,
            amount=inp.amount,
            period_type=inp.period_type,
            category_id=category_id,
            threshold_warning=inp.threshold_warning,
        )
        await self._repo.save(limit)

        return to_limit_output(limit)
