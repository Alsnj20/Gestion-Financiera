from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_payment_method_use_case, build_payment_method_repository
from infrastructure.database.session import get_session
from modules.payment_methods.presentation.schemas import CreatePaymentMethodRequestSchema, PaymentMethodResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])


@router.post("", response_model=PaymentMethodResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_payment_method(payload: CreatePaymentMethodRequestSchema, session: AsyncSession = Depends(get_session)):
    use_case = build_create_payment_method_use_case(session)
    try:
        input_dto = payload.to_input_dto()
        result = await use_case.execute(input_dto)
        await session.commit()
        return PaymentMethodResponseSchema(id=result.id, user_id=result.user_id, account_id=result.account_id, name=result.name, type=result.type, is_default=result.is_default, status=result.status)
    except (ValidationError, ValueError) as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "VALIDATION_ERROR", "message": str(e)}) from e
    except ConflictError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": e.code, "message": e.message}) from e


@router.get("/user/{user_id}", response_model=list[PaymentMethodResponseSchema])
async def list_payment_methods_by_user(user_id: str, session: AsyncSession = Depends(get_session)):
    repo = build_payment_method_repository(session)
    pms = await repo.find_by_user(user_id)
    return [PaymentMethodResponseSchema(id=pm.id, user_id=pm.user_id, account_id=pm.account_id, name=pm.name, type=pm.type, is_default=pm.is_default, status=pm.status.value if hasattr(pm.status, "value") else str(pm.status)) for pm in pms]
