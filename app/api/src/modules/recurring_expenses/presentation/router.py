from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_recurring_expense_use_case, build_recurring_expense_repository
from modules.auth.presentation.dependencies import get_current_user, check_ownership
from infrastructure.database.session import get_session
from modules.recurring_expenses.presentation.schemas import CreateRecurringExpenseRequestSchema, UpdateRecurringExpenseRequestSchema, RecurringExpenseResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/recurring-expenses", tags=["recurring-expenses"])


@router.post("", response_model=RecurringExpenseResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_recurring_expense(payload: CreateRecurringExpenseRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    use_case = build_create_recurring_expense_use_case(session)
    try:
        input_dto = payload.to_input_dto()
        input_dto.user_id = current_user["user_id"]
        result = await use_case.execute(input_dto)
        await session.commit()
        return RecurringExpenseResponseSchema(
            id=result.id, user_id=result.user_id, account_id=result.account_id,
            category_id=result.category_id, amount=result.amount, frequency=result.frequency,
            next_date=result.next_date, description=result.description, status=result.status,
        )
    except (ValidationError, ValueError) as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "VALIDATION_ERROR", "message": str(e)}) from e
    except ConflictError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": e.code, "message": e.message}) from e


@router.get("/user/{user_id}", response_model=list[RecurringExpenseResponseSchema])
async def list_recurring_expenses_by_user(user_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    if user_id != current_user["user_id"] and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    repo = build_recurring_expense_repository(session)
    items = await repo.find_by_user(user_id)
    return [
        RecurringExpenseResponseSchema(
            id=r.id, user_id=r.user_id, account_id=r.account_id,
            category_id=r.category_id, amount=str(r.amount),
            frequency=r.frequency.value if hasattr(r.frequency, "value") else str(r.frequency),
            next_date=str(r.next_date), description=r.description, status=r.status,
        )
        for r in items
    ]


@router.get("/{re_id}", response_model=RecurringExpenseResponseSchema)
async def get_recurring_expense(re_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_recurring_expense_repository(session)
    item = await repo.find_by_id(re_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gasto recurrente no encontrado")
    check_ownership(item, current_user)
    return RecurringExpenseResponseSchema(
        id=item.id, user_id=item.user_id, account_id=item.account_id,
        category_id=item.category_id, amount=str(item.amount),
        frequency=item.frequency.value if hasattr(item.frequency, "value") else str(item.frequency),
        next_date=str(item.next_date), description=item.description, status=item.status,
    )


@router.put("/{re_id}", response_model=RecurringExpenseResponseSchema)
async def update_recurring_expense(re_id: str, payload: UpdateRecurringExpenseRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_recurring_expense_repository(session)
    item = await repo.find_by_id(re_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gasto recurrente no encontrado")
    check_ownership(item, current_user)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(item, field, value)

    await repo.save(item)
    await session.commit()

    return RecurringExpenseResponseSchema(
        id=item.id, user_id=item.user_id, account_id=item.account_id,
        category_id=item.category_id, amount=str(item.amount),
        frequency=item.frequency.value if hasattr(item.frequency, "value") else str(item.frequency),
        next_date=str(item.next_date), description=item.description, status=item.status,
    )


@router.delete("/{re_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring_expense(re_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_recurring_expense_repository(session)
    item = await repo.find_by_id(re_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gasto recurrente no encontrado")
    check_ownership(item, current_user)

    await repo.delete(re_id)
    await session.commit()
