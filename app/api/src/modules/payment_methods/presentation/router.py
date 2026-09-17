"""PaymentMethod Router — Solo enruta, delega al Controller."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from composition import get_payment_method_controller
from modules.auth.presentation.dependencies import get_current_user, require_active_user
from modules.payment_methods.application.use_cases.archive_payment_method import (
    ArchivePaymentMethodInput,
)
from modules.payment_methods.application.use_cases.get_payment_method import (
    GetPaymentMethodInput,
)
from modules.payment_methods.application.use_cases.list_payment_methods import (
    ListPaymentMethodsInput,
)
from modules.payment_methods.application.use_cases.restore_payment_method import (
    RestorePaymentMethodInput,
)
from modules.payment_methods.application.use_cases.update_payment_method import (
    UpdatePaymentMethodInput,
)
from modules.payment_methods.presentation.controllers.payment_method_controller import (
    PaymentMethodController,
)
from modules.payment_methods.presentation.schemas import (
    CreatePaymentMethodRequestSchema,
    PaymentMethodResponseSchema,
    UpdatePaymentMethodRequestSchema,
)

router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])

CurrentUser = Annotated[dict, Depends(get_current_user)]
ActiveUser = Annotated[dict, Depends(require_active_user)]
PaymentMethodCtrl = Annotated[
    PaymentMethodController, Depends(get_payment_method_controller)
]


@router.post(
    "", response_model=PaymentMethodResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_payment_method(
    payload: CreatePaymentMethodRequestSchema,
    current_user: CurrentUser,
    controller: PaymentMethodCtrl,
):
    # user_id sale del JWT, nunca del body.
    result = await controller.create(
        payload.to_input_dto(user_id=current_user["user_id"])
    )
    return PaymentMethodResponseSchema(**result)


@router.get("/user/{user_id}", response_model=list[PaymentMethodResponseSchema])
async def list_payment_methods_by_user(
    user_id: str,
    current_user: CurrentUser,
    controller: PaymentMethodCtrl,
):
    result = await controller.list_by_user(
        ListPaymentMethodsInput(
            user_id=user_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return [PaymentMethodResponseSchema(**item) for item in result]


@router.get("/{pm_id}", response_model=PaymentMethodResponseSchema)
async def get_payment_method(
    pm_id: str,
    current_user: CurrentUser,
    controller: PaymentMethodCtrl,
):
    result = await controller.get(
        GetPaymentMethodInput(
            pm_id=pm_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return PaymentMethodResponseSchema(**result)


@router.put("/{pm_id}", response_model=PaymentMethodResponseSchema)
async def update_payment_method(
    pm_id: str,
    payload: UpdatePaymentMethodRequestSchema,
    current_user: ActiveUser,
    controller: PaymentMethodCtrl,
):
    result = await controller.update(
        UpdatePaymentMethodInput(
            pm_id=pm_id,
            user_id=current_user["user_id"],
            name=payload.name,
            type=payload.type,
            account_id=payload.account_id,
            is_default=payload.is_default,
        )
    )
    return PaymentMethodResponseSchema(**result)


@router.delete("/{pm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_payment_method(
    pm_id: str,
    current_user: ActiveUser,
    controller: PaymentMethodCtrl,
):
    """Archivado lógico (libera el nombre); nunca borrado físico."""
    await controller.archive(
        ArchivePaymentMethodInput(pm_id=pm_id, user_id=current_user["user_id"])
    )


@router.post("/{pm_id}/restore", response_model=PaymentMethodResponseSchema)
async def restore_payment_method(
    pm_id: str,
    current_user: ActiveUser,
    controller: PaymentMethodCtrl,
):
    result = await controller.restore(
        RestorePaymentMethodInput(pm_id=pm_id, user_id=current_user["user_id"])
    )
    return PaymentMethodResponseSchema(**result)
