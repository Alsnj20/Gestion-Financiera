"""Debt Router — Solo enruta, delega al Controller."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from composition import get_debt_controller
from modules.auth.presentation.dependencies import get_current_user, require_active_user
from modules.debts.application.use_cases.cancel_debt import CancelDebtInput
from modules.debts.application.use_cases.get_debt import GetDebtInput
from modules.debts.application.use_cases.list_debts import ListDebtsInput
from modules.debts.application.use_cases.register_debt_payment import (
    RegisterDebtPaymentInput,
)
from modules.debts.application.use_cases.update_debt import UpdateDebtInput
from modules.debts.presentation.controllers.debt_controller import DebtController
from modules.debts.presentation.schemas import (
    CreateDebtRequestSchema,
    DebtResponseSchema,
    RegisterPaymentRequestSchema,
    RegisterPaymentResponseSchema,
    UpdateDebtRequestSchema,
)

router = APIRouter(prefix="/debts", tags=["debts"])

CurrentUser = Annotated[dict, Depends(get_current_user)]
ActiveUser = Annotated[dict, Depends(require_active_user)]
DebtCtrl = Annotated[DebtController, Depends(get_debt_controller)]


@router.post("", response_model=DebtResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_debt(
    payload: CreateDebtRequestSchema,
    current_user: CurrentUser,
    controller: DebtCtrl,
):
    # user_id sale del JWT, nunca del body.
    result = await controller.create(
        payload.to_input_dto(user_id=current_user["user_id"])
    )
    return DebtResponseSchema(**result)


@router.get("/user/{user_id}", response_model=list[DebtResponseSchema])
async def list_debts_by_user(
    user_id: str,
    current_user: CurrentUser,
    controller: DebtCtrl,
):
    result = await controller.list_by_user(
        ListDebtsInput(
            user_id=user_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return [DebtResponseSchema(**item) for item in result]


@router.get("/{debt_id}", response_model=DebtResponseSchema)
async def get_debt(
    debt_id: str,
    current_user: CurrentUser,
    controller: DebtCtrl,
):
    result = await controller.get(
        GetDebtInput(
            debt_id=debt_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return DebtResponseSchema(**result)


@router.put("/{debt_id}", response_model=DebtResponseSchema)
async def update_debt(
    debt_id: str,
    payload: UpdateDebtRequestSchema,
    current_user: ActiveUser,
    controller: DebtCtrl,
):
    """Solo metadatos (creditor_name/notes): el principal no se edita."""
    result = await controller.update(
        UpdateDebtInput(
            debt_id=debt_id,
            requester_id=current_user["user_id"],
            creditor_name=payload.creditor_name,
            notes=payload.notes,
        )
    )
    return DebtResponseSchema(**result)


@router.post("/{debt_id}/cancel", response_model=DebtResponseSchema)
async def cancel_debt(
    debt_id: str,
    current_user: ActiveUser,
    controller: DebtCtrl,
):
    """Anulación lógica: la fila se conserva con CANCELLED, nunca se borra."""
    result = await controller.cancel(
        CancelDebtInput(debt_id=debt_id, requester_id=current_user["user_id"])
    )
    return DebtResponseSchema(**result)


@router.post(
    "/{debt_id}/payments",
    response_model=RegisterPaymentResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def register_debt_payment(
    debt_id: str,
    payload: RegisterPaymentRequestSchema,
    current_user: ActiveUser,
    controller: DebtCtrl,
):
    """Registra un pago: EXPENSE de la cuenta + cuota + balance. Cierra en PAID."""
    result = await controller.register_payment(
        RegisterDebtPaymentInput(
            debt_id=debt_id,
            requester_id=current_user["user_id"],
            account_id=payload.account_id,
            installment_id=payload.installment_id,
            principal_amount=payload.principal_amount,
            interest_amount=payload.interest_amount,
            payment_date=payload.payment_date,
            category_id=payload.category_id,
            payment_method_id=payload.payment_method_id,
            description=payload.description,
        )
    )
    return RegisterPaymentResponseSchema(**result)
