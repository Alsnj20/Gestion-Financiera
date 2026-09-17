from __future__ import annotations

from dataclasses import dataclass

from modules.categories.application.dtos import UpdateCategoryOutput, to_category_output
from modules.categories.application.ports.category_repository import (
    CategoryRepositoryPort,
)
from modules.categories.application.use_cases.create_category import (
    _ensure_no_cycle,
    _resolve_parent,
)
from shared.errors import BusinessRuleError, ConflictError, NotFoundError


@dataclass(frozen=True, slots=True)
class UpdateCategoryInput:
    category_id: str
    user_id: str
    name: str | None = None
    type: str | None = None
    parent_id: str | None = None


class UpdateCategoryUseCase:
    def __init__(self, repo: CategoryRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: UpdateCategoryInput) -> UpdateCategoryOutput:
        category = await self._repo.find_by_id(inp.category_id)

        if category is None:
            raise NotFoundError(
                code="CAT_NOT_FOUND",
                message="Categoría no encontrada",
            )

        # Escritura: solo el dueño (admin solo lee el ledger ajeno).
        if category.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )
        if category.is_archived():
            raise BusinessRuleError(
                code="CAT_ARCHIVED",
                message="Categoría archivada no se puede editar. Restaúrala primero.",
            )

        if inp.parent_id is not None and inp.parent_id != category.parent_id:
            new_parent = await _resolve_parent(self._repo, inp.user_id, inp.parent_id)
            await _ensure_no_cycle(self._repo, category.id, new_parent)
            category = category.reparent(new_parent)

        if inp.name is not None and inp.name != category.name:
            if await self._repo.exists_name_for_user(
                inp.user_id, inp.name, category.parent_id
            ):
                raise ConflictError(
                    code="CAT_NAME_TAKEN",
                    message=f"Nombre ya existe: {inp.name}",
                )
            category = category.rename(inp.name)

        if inp.type is not None:
            category = category.change_type(inp.type)

        await self._repo.save(category)

        return to_category_output(category)
