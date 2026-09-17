"""Budget Router — Solo enruta, delega al Controller."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from composition import get_budget_controller
from modules.auth.presentation.dependencies import get_current_user, require_active_user
from modules.budgets.application.use_cases.archive_budget import ArchiveBudgetInput
from modules.budgets.application.use_cases.get_budget import GetBudgetInput
from modules.budgets.application.use_cases.list_budgets import ListBudgetsInput
from modules.budgets.application.use_cases.restore_budget import RestoreBudgetInput
from modules.budgets.application.use_cases.update_budget import UpdateBudgetInput
from modules.budgets.presentation.controllers.budget_controller import BudgetController
from modules.budgets.presentation.schemas import (
    BudgetResponseSchema,
    CreateBudgetRequestSchema,
    UpdateBudgetRequestSchema,
)

router = APIRouter(prefix="/budgets", tags=["budgets"])

CurrentUser = Annotated[dict, Depends(get_current_user)]
ActiveUser = Annotated[dict, Depends(require_active_user)]
BudgetCtrl = Annotated[BudgetController, Depends(get_budget_controller)]


@router.post(
    "", response_model=BudgetResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_budget(
    payload: CreateBudgetRequestSchema,
    current_user: CurrentUser,
    controller: BudgetCtrl,
):
    # user_id sale del JWT, nunca del body.
    result = await controller.create(
        payload.to_input_dto(user_id=current_user["user_id"])
    )
    return BudgetResponseSchema(**result)


@router.get("/user/{user_id}", response_model=list[BudgetResponseSchema])
async def list_budgets_by_user(
    user_id: str,
    current_user: CurrentUser,
    controller: BudgetCtrl,
    include_archived: bool = Query(default=False),
):
    result = await controller.list_by_user(
        ListBudgetsInput(
            user_id=user_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
            include_archived=include_archived,
        )
    )
    return [BudgetResponseSchema(**item) for item in result]


@router.get("/{budget_id}", response_model=BudgetResponseSchema)
async def get_budget(
    budget_id: str,
    current_user: CurrentUser,
    controller: BudgetCtrl,
):
    result = await controller.get(
        GetBudgetInput(
            budget_id=budget_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return BudgetResponseSchema(**result)


@router.put("/{budget_id}", response_model=BudgetResponseSchema)
async def update_budget(
    budget_id: str,
    payload: UpdateBudgetRequestSchema,
    current_user: ActiveUser,
    controller: BudgetCtrl,
):
    result = await controller.update(
        UpdateBudgetInput(
            budget_id=budget_id,
            user_id=current_user["user_id"],
            name=payload.name,
            amount=payload.amount,
            period_start=payload.period_start,
            period_end=payload.period_end,
            category_id=payload.category_id,
        )
    )
    return BudgetResponseSchema(**result)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_budget(
    budget_id: str,
    current_user: ActiveUser,
    controller: BudgetCtrl,
):
    """Archivado lógico; nunca borrado físico."""
    await controller.archive(
        ArchiveBudgetInput(budget_id=budget_id, user_id=current_user["user_id"])
    )


@router.post("/{budget_id}/restore", response_model=BudgetResponseSchema)
async def restore_budget(
    budget_id: str,
    current_user: ActiveUser,
    controller: BudgetCtrl,
):
    result = await controller.restore(
        RestoreBudgetInput(budget_id=budget_id, user_id=current_user["user_id"])
    )
    return BudgetResponseSchema(**result)
