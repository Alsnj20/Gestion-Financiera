"""RecurringExpense Router — Solo enruta, delega al Controller."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from composition import get_recurring_expense_controller
from modules.auth.presentation.dependencies import get_current_user, require_active_user
from modules.recurring_expenses.application.use_cases.cancel_recurring_expense import (
    CancelRecurringExpenseInput,
)
from modules.recurring_expenses.application.use_cases.get_recurring_expense import (
    GetRecurringExpenseInput,
)
from modules.recurring_expenses.application.use_cases.list_recurring_expenses import (
    ListRecurringExpensesInput,
)
from modules.recurring_expenses.application.use_cases.pause_recurring_expense import (
    PauseRecurringExpenseInput,
)
from modules.recurring_expenses.application.use_cases.resume_recurring_expense import (
    ResumeRecurringExpenseInput,
)
from modules.recurring_expenses.application.use_cases.update_recurring_expense import (
    UpdateRecurringExpenseInput,
)
from modules.recurring_expenses.presentation.controllers.recurring_expense_controller import (
    RecurringExpenseController,
)
from modules.recurring_expenses.presentation.schemas import (
    CreateRecurringExpenseRequestSchema,
    RecurringExpenseResponseSchema,
    UpdateRecurringExpenseRequestSchema,
)

router = APIRouter(prefix="/recurring-expenses", tags=["recurring-expenses"])

CurrentUser = Annotated[dict, Depends(get_current_user)]
ActiveUser = Annotated[dict, Depends(require_active_user)]
RecurringExpenseCtrl = Annotated[
    RecurringExpenseController, Depends(get_recurring_expense_controller)
]


@router.post(
    "",
    response_model=RecurringExpenseResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_recurring_expense(
    payload: CreateRecurringExpenseRequestSchema,
    current_user: CurrentUser,
    controller: RecurringExpenseCtrl,
):
    # user_id sale del JWT, nunca del body.
    result = await controller.create(
        payload.to_input_dto(user_id=current_user["user_id"])
    )
    return RecurringExpenseResponseSchema(**result)


@router.get("/user/{user_id}", response_model=list[RecurringExpenseResponseSchema])
async def list_recurring_expenses_by_user(
    user_id: str,
    current_user: CurrentUser,
    controller: RecurringExpenseCtrl,
):
    result = await controller.list_by_user(
        ListRecurringExpensesInput(
            user_id=user_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return [RecurringExpenseResponseSchema(**item) for item in result]


@router.get("/{re_id}", response_model=RecurringExpenseResponseSchema)
async def get_recurring_expense(
    re_id: str,
    current_user: CurrentUser,
    controller: RecurringExpenseCtrl,
):
    result = await controller.get(
        GetRecurringExpenseInput(
            re_id=re_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return RecurringExpenseResponseSchema(**result)


@router.put("/{re_id}", response_model=RecurringExpenseResponseSchema)
async def update_recurring_expense(
    re_id: str,
    payload: UpdateRecurringExpenseRequestSchema,
    current_user: ActiveUser,
    controller: RecurringExpenseCtrl,
):
    result = await controller.update(
        UpdateRecurringExpenseInput(
            re_id=re_id,
            user_id=current_user["user_id"],
            amount=payload.amount,
            frequency=payload.frequency,
            next_date=payload.next_date,
            description=payload.description,
            category_id=payload.category_id,
        )
    )
    return RecurringExpenseResponseSchema(**result)


@router.post("/{re_id}/pause", response_model=RecurringExpenseResponseSchema)
async def pause_recurring_expense(
    re_id: str,
    current_user: ActiveUser,
    controller: RecurringExpenseCtrl,
):
    """Transición → PAUSED (la cuenta no se toca)."""
    result = await controller.pause(
        PauseRecurringExpenseInput(re_id=re_id, user_id=current_user["user_id"])
    )
    return RecurringExpenseResponseSchema(**result)


@router.post("/{re_id}/resume", response_model=RecurringExpenseResponseSchema)
async def resume_recurring_expense(
    re_id: str,
    current_user: ActiveUser,
    controller: RecurringExpenseCtrl,
):
    """Transición → ACTIVE."""
    result = await controller.resume(
        ResumeRecurringExpenseInput(re_id=re_id, user_id=current_user["user_id"])
    )
    return RecurringExpenseResponseSchema(**result)


@router.post("/{re_id}/cancel", response_model=RecurringExpenseResponseSchema)
async def cancel_recurring_expense(
    re_id: str,
    current_user: ActiveUser,
    controller: RecurringExpenseCtrl,
):
    """Anulación lógica: la fila se conserva con CANCELLED, nunca se borra."""
    result = await controller.cancel(
        CancelRecurringExpenseInput(re_id=re_id, user_id=current_user["user_id"])
    )
    return RecurringExpenseResponseSchema(**result)
