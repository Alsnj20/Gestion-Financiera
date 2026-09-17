"""Category Router — Solo enruta, delega al Controller."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from composition import get_category_controller
from modules.auth.presentation.dependencies import get_current_user, require_active_user
from modules.categories.application.use_cases.archive_category import (
    ArchiveCategoryInput,
)
from modules.categories.application.use_cases.get_category import GetCategoryInput
from modules.categories.application.use_cases.list_categories import ListCategoriesInput
from modules.categories.application.use_cases.restore_category import (
    RestoreCategoryInput,
)
from modules.categories.application.use_cases.update_category import UpdateCategoryInput
from modules.categories.presentation.controllers.category_controller import (
    CategoryController,
)
from modules.categories.presentation.schemas import (
    CategoryResponseSchema,
    CreateCategoryRequestSchema,
    UpdateCategoryRequestSchema,
)

router = APIRouter(prefix="/categories", tags=["categories"])

CurrentUser = Annotated[dict, Depends(get_current_user)]
ActiveUser = Annotated[dict, Depends(require_active_user)]
CategoryCtrl = Annotated[CategoryController, Depends(get_category_controller)]


@router.post(
    "", response_model=CategoryResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_category(
    payload: CreateCategoryRequestSchema,
    current_user: CurrentUser,
    controller: CategoryCtrl,
):
    # user_id sale del JWT, nunca del body.
    result = await controller.create(
        payload.to_input_dto(user_id=current_user["user_id"])
    )
    return CategoryResponseSchema(**result)


@router.get("/user/{user_id}", response_model=list[CategoryResponseSchema])
async def list_categories_by_user(
    user_id: str,
    current_user: CurrentUser,
    controller: CategoryCtrl,
    include_archived: bool = Query(default=False),
):
    result = await controller.list_by_user(
        ListCategoriesInput(
            user_id=user_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
            include_archived=include_archived,
        )
    )
    return [CategoryResponseSchema(**item) for item in result]


@router.get("/{category_id}", response_model=CategoryResponseSchema)
async def get_category(
    category_id: str,
    current_user: CurrentUser,
    controller: CategoryCtrl,
):
    result = await controller.get(
        GetCategoryInput(
            category_id=category_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return CategoryResponseSchema(**result)


@router.put("/{category_id}", response_model=CategoryResponseSchema)
async def update_category(
    category_id: str,
    payload: UpdateCategoryRequestSchema,
    current_user: ActiveUser,
    controller: CategoryCtrl,
):
    result = await controller.update(
        UpdateCategoryInput(
            category_id=category_id,
            user_id=current_user["user_id"],
            name=payload.name,
            type=payload.type,
            parent_id=payload.parent_id,
        )
    )
    return CategoryResponseSchema(**result)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_category(
    category_id: str,
    current_user: ActiveUser,
    controller: CategoryCtrl,
):
    """Archivado lógico (libera el nombre); nunca borrado físico."""
    await controller.archive(
        ArchiveCategoryInput(category_id=category_id, user_id=current_user["user_id"])
    )


@router.post("/{category_id}/restore", response_model=CategoryResponseSchema)
async def restore_category(
    category_id: str,
    current_user: ActiveUser,
    controller: CategoryCtrl,
):
    result = await controller.restore(
        RestoreCategoryInput(category_id=category_id, user_id=current_user["user_id"])
    )
    return CategoryResponseSchema(**result)
