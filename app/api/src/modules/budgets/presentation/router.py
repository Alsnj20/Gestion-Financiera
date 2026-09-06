from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_budget_use_case, build_budget_repository
from modules.auth.presentation.dependencies import get_current_user, check_ownership
from infrastructure.database.session import get_session
from modules.budgets.presentation.schemas import CreateBudgetRequestSchema, UpdateBudgetRequestSchema, BudgetResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=BudgetResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_budget(payload: CreateBudgetRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    use_case = build_create_budget_use_case(session)
    try:
        input_dto = payload.to_input_dto()
        input_dto.user_id = current_user["user_id"]
        result = await use_case.execute(input_dto)
        await session.commit()
        return BudgetResponseSchema(id=result.id, user_id=result.user_id, name=result.name, amount=result.amount, period_start=result.period_start, period_end=result.period_end, category_id=result.category_id, status=result.status)
    except (ValidationError, ValueError) as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "VALIDATION_ERROR", "message": str(e)}) from e
    except ConflictError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": e.code, "message": e.message}) from e


@router.get("/user/{user_id}", response_model=list[BudgetResponseSchema])
async def list_budgets_by_user(user_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    if user_id != current_user["user_id"] and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    repo = build_budget_repository(session)
    budgets = await repo.find_by_user(user_id)
    return [BudgetResponseSchema(id=b.id, user_id=b.user_id, name=b.name, amount=b.amount, period_start=b.period_start, period_end=b.period_end, category_id=b.category_id, status=b.status.value if hasattr(b.status, "value") else str(b.status)) for b in budgets]


@router.get("/{budget_id}", response_model=BudgetResponseSchema)
async def get_budget(budget_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_budget_repository(session)
    budget = await repo.find_by_id(budget_id)
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presupuesto no encontrado")
    check_ownership(budget, current_user)
    return BudgetResponseSchema(
        id=budget.id, user_id=budget.user_id, name=budget.name, amount=budget.amount,
        period_start=budget.period_start, period_end=budget.period_end,
        category_id=budget.category_id,
        status=budget.status.value if hasattr(budget.status, "value") else str(budget.status),
    )


@router.put("/{budget_id}", response_model=BudgetResponseSchema)
async def update_budget(budget_id: str, payload: UpdateBudgetRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_budget_repository(session)
    budget = await repo.find_by_id(budget_id)
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presupuesto no encontrado")
    check_ownership(budget, current_user)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(budget, field, value)

    await repo.save(budget)
    await session.commit()

    return BudgetResponseSchema(
        id=budget.id, user_id=budget.user_id, name=budget.name, amount=budget.amount,
        period_start=budget.period_start, period_end=budget.period_end,
        category_id=budget.category_id,
        status=budget.status.value if hasattr(budget.status, "value") else str(budget.status),
    )


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(budget_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_budget_repository(session)
    budget = await repo.find_by_id(budget_id)
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presupuesto no encontrado")
    check_ownership(budget, current_user)

    await repo.delete(budget_id)
    await session.commit()
