"""Transaction Router — Solo enruta, delega al Controller."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status

from composition import get_transaction_controller
from modules.auth.presentation.dependencies import get_current_user, require_active_user
from modules.transactions.application.use_cases.cancel_transaction import (
    CancelTransactionInput,
)
from modules.transactions.application.use_cases.get_transaction import (
    GetTransactionInput,
)
from modules.transactions.application.use_cases.list_transactions import (
    ListTransactionsInput,
)
from modules.transactions.application.use_cases.update_transaction import (
    UpdateTransactionInput,
)
from modules.transactions.presentation.controllers.transaction_controller import (
    TransactionController,
)
from modules.transactions.presentation.schemas import (
    CreateTransactionRequestSchema,
    TransactionResponseSchema,
    UpdateTransactionRequestSchema,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])

CurrentUser = Annotated[dict, Depends(get_current_user)]
ActiveUser = Annotated[dict, Depends(require_active_user)]
TxCtrl = Annotated[TransactionController, Depends(get_transaction_controller)]


@router.post(
    "", response_model=TransactionResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    payload: CreateTransactionRequestSchema,
    current_user: CurrentUser,
    controller: TxCtrl,
):
    # user_id sale del JWT, nunca del body.
    result = await controller.create(
        payload.to_input_dto(user_id=current_user["user_id"])
    )
    return TransactionResponseSchema(**result)


@router.get("/{tx_id}", response_model=TransactionResponseSchema)
async def get_transaction(
    tx_id: str,
    current_user: CurrentUser,
    controller: TxCtrl,
):
    result = await controller.get(
        GetTransactionInput(
            tx_id=tx_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return TransactionResponseSchema(**result)


@router.get("/user/{user_id}", response_model=list[TransactionResponseSchema])
async def list_transactions_by_user(
    user_id: str,
    current_user: CurrentUser,
    controller: TxCtrl,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    account_id: str | None = None,
    type: str | None = None,
):
    result = await controller.list_by_user(
        ListTransactionsInput(
            user_id=user_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
            from_date=from_date,
            to_date=to_date,
            account_id=account_id,
            type=type,
        )
    )
    return [TransactionResponseSchema(**item) for item in result]


@router.put("/{tx_id}", response_model=TransactionResponseSchema)
async def update_transaction(
    tx_id: str,
    payload: UpdateTransactionRequestSchema,
    current_user: ActiveUser,
    controller: TxCtrl,
):
    """Solo metadatos (concepto/category/payment_method).

    amount/type/account_id son inmutables: para corregir un monto se
    cancela y se recrea, así el balance nunca se descuadra.
    """
    result = await controller.update(
        UpdateTransactionInput(
            tx_id=tx_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
            concepto=payload.concepto,
            category_id=payload.category_id,
            payment_method_id=payload.payment_method_id,
        )
    )
    return TransactionResponseSchema(**result)


@router.post("/{tx_id}/cancel", response_model=TransactionResponseSchema)
async def cancel_transaction(
    tx_id: str,
    current_user: ActiveUser,
    controller: TxCtrl,
):
    """Cancela revirtiendo el efecto en el balance. Idempotente.

    Es la única vía de anulación: el libro mayor no se borra,
    se cancela (la fila se conserva con status CANCELLED).
    """
    result = await controller.cancel(
        CancelTransactionInput(
            tx_id=tx_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return TransactionResponseSchema(**result)
