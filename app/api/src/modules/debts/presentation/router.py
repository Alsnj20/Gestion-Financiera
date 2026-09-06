from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_debt_use_case, build_debt_repository
from infrastructure.database.session import get_session
from modules.debts.presentation.schemas import CreateDebtRequestSchema, DebtResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/debts", tags=["debts"])


@router.post("", response_model=DebtResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_debt(payload: CreateDebtRequestSchema, session: AsyncSession = Depends(get_session)):
    use_case = build_create_debt_use_case(session)
    try:
        input_dto = payload.to_input_dto()
        result = await use_case.execute(input_dto)
        await session.commit()
        return DebtResponseSchema(id=result.id, user_id=result.user_id, creditor_name=result.creditor_name, principal_amount=result.principal_amount, status=result.status)
    except (ValidationError, ValueError) as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "VALIDATION_ERROR", "message": str(e)}) from e
    except ConflictError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": e.code, "message": e.message}) from e


@router.get("/user/{user_id}", response_model=list[DebtResponseSchema])
async def list_debts_by_user(user_id: str, session: AsyncSession = Depends(get_session)):
    repo = build_debt_repository(session)
    debts = await repo.find_by_user(user_id)
    return [DebtResponseSchema(id=d.id, user_id=d.user_id, creditor_name=d.creditor_name, principal_amount=d.principal_amount, status=d.status.value if hasattr(d.status, "value") else str(d.status)) for d in debts]
