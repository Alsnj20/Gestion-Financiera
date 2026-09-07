"""Transfer Router — Solo enruta, delega al Controller."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from composition import get_transfer_controller
from modules.auth.presentation.dependencies import get_current_user
from modules.transfers.application.use_cases.get_transfer import GetTransferInput
from modules.transfers.application.use_cases.reverse_transfer import (
    ReverseTransferInput,
)
from modules.transfers.presentation.controllers.transfer_controller import (
    TransferController,
)
from modules.transfers.presentation.schemas import (
    CreateTransferRequestSchema,
    TransferResponseSchema,
)

router = APIRouter(prefix="/transfers", tags=["transfers"])

CurrentUser = Annotated[dict, Depends(get_current_user)]
TransferCtrl = Annotated[TransferController, Depends(get_transfer_controller)]


@router.post(
    "", response_model=TransferResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_transfer(
    payload: CreateTransferRequestSchema,
    current_user: CurrentUser,
    controller: TransferCtrl,
):
    # user_id sale del JWT, nunca del body.
    result = await controller.create(
        payload.to_input_dto(user_id=current_user["user_id"])
    )
    return TransferResponseSchema(**result)


@router.get("/{transfer_id}", response_model=TransferResponseSchema)
async def get_transfer(
    transfer_id: str,
    current_user: CurrentUser,
    controller: TransferCtrl,
):
    result = await controller.get(
        GetTransferInput(
            transfer_id=transfer_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return TransferResponseSchema(**result)


@router.post("/{transfer_id}/reverse", response_model=TransferResponseSchema)
async def reverse_transfer(
    transfer_id: str,
    current_user: CurrentUser,
    controller: TransferCtrl,
):
    """Revierte la transferencia: deshace balances, marca patas y elimina el agregado."""
    result = await controller.reverse(
        ReverseTransferInput(
            transfer_id=transfer_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return TransferResponseSchema(**result)
