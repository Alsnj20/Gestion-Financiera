"""Loan Router — Solo enruta, delega al Controller."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from composition import get_loan_controller
from modules.auth.presentation.dependencies import get_current_user, require_active_user
from modules.loans.application.use_cases.cancel_loan import CancelLoanInput
from modules.loans.application.use_cases.get_loan import GetLoanInput
from modules.loans.application.use_cases.list_loans import ListLoansInput
from modules.loans.application.use_cases.register_loan_payment import (
    RegisterLoanPaymentInput,
)
from modules.loans.application.use_cases.update_loan import UpdateLoanInput
from modules.loans.presentation.controllers.loan_controller import LoanController
from modules.loans.presentation.schemas import (
    CreateLoanRequestSchema,
    LoanResponseSchema,
    RegisterPaymentRequestSchema,
    RegisterPaymentResponseSchema,
    UpdateLoanRequestSchema,
)

router = APIRouter(prefix="/loans", tags=["loans"])

CurrentUser = Annotated[dict, Depends(get_current_user)]
ActiveUser = Annotated[dict, Depends(require_active_user)]
LoanCtrl = Annotated[LoanController, Depends(get_loan_controller)]


@router.post("", response_model=LoanResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_loan(
    payload: CreateLoanRequestSchema,
    current_user: CurrentUser,
    controller: LoanCtrl,
):
    # user_id sale del JWT, nunca del body.
    result = await controller.create(
        payload.to_input_dto(user_id=current_user["user_id"])
    )
    return LoanResponseSchema(**result)


@router.get("/user/{user_id}", response_model=list[LoanResponseSchema])
async def list_loans_by_user(
    user_id: str,
    current_user: CurrentUser,
    controller: LoanCtrl,
):
    result = await controller.list_by_user(
        ListLoansInput(
            user_id=user_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return [LoanResponseSchema(**item) for item in result]


@router.get("/{loan_id}", response_model=LoanResponseSchema)
async def get_loan(
    loan_id: str,
    current_user: CurrentUser,
    controller: LoanCtrl,
):
    result = await controller.get(
        GetLoanInput(
            loan_id=loan_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return LoanResponseSchema(**result)


@router.put("/{loan_id}", response_model=LoanResponseSchema)
async def update_loan(
    loan_id: str,
    payload: UpdateLoanRequestSchema,
    current_user: ActiveUser,
    controller: LoanCtrl,
):
    """Solo metadatos (borrower_name/notes): el principal no se edita."""
    result = await controller.update(
        UpdateLoanInput(
            loan_id=loan_id,
            requester_id=current_user["user_id"],
            borrower_name=payload.borrower_name,
            notes=payload.notes,
        )
    )
    return LoanResponseSchema(**result)


@router.post("/{loan_id}/cancel", response_model=LoanResponseSchema)
async def cancel_loan(
    loan_id: str,
    current_user: ActiveUser,
    controller: LoanCtrl,
):
    """Anulación lógica: la fila se conserva con CANCELLED, nunca se borra."""
    result = await controller.cancel(
        CancelLoanInput(loan_id=loan_id, requester_id=current_user["user_id"])
    )
    return LoanResponseSchema(**result)


@router.post(
    "/{loan_id}/payments",
    response_model=RegisterPaymentResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def register_loan_payment(
    loan_id: str,
    payload: RegisterPaymentRequestSchema,
    current_user: ActiveUser,
    controller: LoanCtrl,
):
    """Registra un cobro: INCOME a la cuenta + cuota + balance. Cierra en PAID."""
    result = await controller.register_payment(
        RegisterLoanPaymentInput(
            loan_id=loan_id,
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
