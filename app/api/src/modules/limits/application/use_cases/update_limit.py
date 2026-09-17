from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from modules.categories.application.ports.category_repository import (
    CategoryRepositoryPort,
)
from modules.limits.application.dtos import UpdateLimitOutput, to_limit_output
from modules.limits.application.ports.limit_repository import LimitRepositoryPort
from modules.limits.application.use_cases.create_limit import _resolve_category
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class UpdateLimitInput:
    limit_id: str
    user_id: str
    name: str | None = None
    amount: Decimal | None = None
    period_type: str | None = None
    category_id: str | None = None
    threshold_warning: Decimal | None = None


class UpdateLimitUseCase:
    def __init__(
        self, repo: LimitRepositoryPort, category_repo: CategoryRepositoryPort
    ) -> None:
        self._repo = repo
        self._category_repo = category_repo

    async def execute(self, inp: UpdateLimitInput) -> UpdateLimitOutput:
        limit = await self._repo.find_by_id(inp.limit_id)

        if limit is None:
            raise NotFoundError(
                code="LIMIT_NOT_FOUND",
                message="Límite no encontrado",
            )

        # Escritura: solo el dueño (admin solo lee el ledger ajeno).
        if limit.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )
        if limit.is_archived():
            raise BusinessRuleError(
                code="LIMIT_ARCHIVED",
                message="Límite archivado no se puede editar. Restaúralo primero.",
            )

        category_id = limit.category_id
        if inp.category_id is not None and inp.category_id != limit.category_id:
            category_id = await _resolve_category(
                self._category_repo, inp.user_id, inp.category_id
            )

        updated = limit.update_details(
            name=inp.name,
            amount=inp.amount,
            period_type=inp.period_type,
            category_id=category_id,
            threshold_warning=inp.threshold_warning,
        )
        await self._repo.save(updated)

        return to_limit_output(updated)
