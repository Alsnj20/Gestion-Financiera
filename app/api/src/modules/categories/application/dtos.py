"""DTOs de salida unificados del módulo categories.

Fuente única: `CategoryOutput` + `to_category_output`.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.categories.domain.entities.category import Category


@dataclass(frozen=True, slots=True)
class CategoryOutput:
    id: str
    user_id: str
    name: str
    type: str
    parent_id: str
    status: str


def to_category_output(category: Category) -> CategoryOutput:
    return CategoryOutput(
        id=category.id,
        user_id=category.user_id,
        name=category.name,
        type=category.type.value,
        parent_id=category.parent_id,
        status=category.status.value,
    )


# Aliases de compatibilidad.
CreateCategoryOutput = CategoryOutput
GetCategoryOutput = CategoryOutput
ListCategoriesOutput = CategoryOutput
UpdateCategoryOutput = CategoryOutput
RestoreCategoryOutput = CategoryOutput
