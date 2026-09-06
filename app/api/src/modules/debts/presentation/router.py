from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_debt_use_case, build_debt_repository
from modules.auth.presentation.dependencies import get_current_user, check_ownership
from infrastructure.database.session import get_session
from modules.debts.presentation.schemas import CreateDebtRequestSchema, UpdateDebtRequestSchema, DebtResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/debts", tags=["debts"])


@router.post("", response_model=DebtResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_debt(payload: CreateDebtRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    use_case = build_create_debt_use_case(session)
    try:
        input_dto = payload.to_input_dto()
        input_dto.user_id = current_user["user_id"]
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
async def list_debts_by_user(user_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    if user_id != current_user["user_id"] and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    repo = build_debt_repository(session)
    debts = await repo.find_by_user(user_id)
    return [DebtResponseSchema(id=d.id, user_id=d.user_id, creditor_name=d.creditor_name, principal_amount=d.principal_amount, status=d.status.value if hasattr(d.status, "value") else str(d.status)) for d in debts]


@router.get("/{debt_id}", response_model=DebtResponseSchema)
async def get_debt(debt_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_debt_repository(session)
    debt = await repo.find_by_id(debt_id)
    if not debt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deuda no encontrada")
    check_ownership(debt, current_user)
    return DebtResponseSchema(
        id=debt.id, user_id=debt.user_id, creditor_name=debt.creditor_name,
        principal_amount=debt.principal_amount,
        status=debt.status.value if hasattr(debt.status, "value") else str(debt.status),
    )


@router.put("/{debt_id}", response_model=DebtResponseSchema)
async def update_debt(debt_id: str, payload: UpdateDebtRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_debt_repository(session)
    debt = await repo.find_by_id(debt_id)
    if not debt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deuda no encontrada")
    check_ownership(debt, current_user)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(debt, field, value)

    await repo.save(debt)
    await session.commit()

    return DebtResponseSchema(
        id=debt.id, user_id=debt.user_id, creditor_name=debt.creditor_name,
        principal_amount=debt.principal_amount,
        status=debt.status.value if hasattr(debt.status, "value") else str(debt.status),
    )


@router.delete("/{debt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_debt(debt_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_debt_repository(session)
    debt = await repo.find_by_id(debt_id)
    if not debt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deuda no encontrada")
    check_ownership(debt, current_user)

    await repo.delete(debt_id)
    await session.commit()
