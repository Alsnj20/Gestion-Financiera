from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_transfer_use_case
from infrastructure.database.session import get_session
from modules.transfers.presentation.schemas import CreateTransferRequestSchema, TransferResponseSchema
from shared.errors import BusinessRuleError, ConflictError, ValidationError

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", response_model=TransferResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_transfer(payload: CreateTransferRequestSchema, session: AsyncSession = Depends(get_session)):
    use_case = build_create_transfer_use_case(session)
    try:
        input_dto = payload.to_input_dto()
        result = await use_case.execute(input_dto)
        await session.commit()
        return TransferResponseSchema(id=result.id, user_id=result.user_id, source_account_id=result.source_account_id, destination_account_id=result.destination_account_id, amount=result.amount, currency=result.currency)
    except (ValidationError, ValueError) as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "VALIDATION_ERROR", "message": str(e)}) from e
    except ConflictError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": e.code, "message": e.message}) from e
    except BusinessRuleError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": e.code, "message": e.message}) from e
