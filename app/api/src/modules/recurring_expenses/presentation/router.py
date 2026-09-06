from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_recurring_expense_use_case, build_recurring_expense_repository
from infrastructure.database.session import get_session
from modules.recurring_expenses.presentation.schemas import CreateRecurringExpenseRequestSchema, RecurringExpenseResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/recurring-expenses", tags=["recurring-expenses"])


@router.post("", response_model=RecurringExpenseResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_recurring_expense(payload: CreateRecurringExpenseRequestSchema, session: AsyncSession = Depends(get_session)):
    use_case = build_create_recurring_expense_use_case(session)
    try:
        input_dto = payload.to_input_dto()
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
async def list_recurring_expenses_by_user(user_id: str, session: AsyncSession = Depends(get_session)):
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
