from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_limit_use_case, build_limit_repository
from modules.auth.presentation.dependencies import get_current_user, check_ownership
from infrastructure.database.session import get_session
from modules.limits.presentation.schemas import CreateLimitRequestSchema, UpdateLimitRequestSchema, LimitResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/limits", tags=["limits"])


@router.post("", response_model=LimitResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_limit(payload: CreateLimitRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    use_case = build_create_limit_use_case(session)
    try:
        input_dto = payload.to_input_dto()
        input_dto.user_id = current_user["user_id"]
        result = await use_case.execute(input_dto)
        await session.commit()
        return LimitResponseSchema(id=result.id, user_id=result.user_id, name=result.name, amount=result.amount, period_type=result.period_type, category_id=result.category_id, threshold_warning=result.threshold_warning, status=result.status)
    except (ValidationError, ValueError) as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "VALIDATION_ERROR", "message": str(e)}) from e
    except ConflictError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": e.code, "message": e.message}) from e


@router.get("/user/{user_id}", response_model=list[LimitResponseSchema])
async def list_limits_by_user(user_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    if user_id != current_user["user_id"] and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    repo = build_limit_repository(session)
    limits = await repo.find_by_user(user_id)
    return [LimitResponseSchema(id=l.id, user_id=l.user_id, name=l.name, amount=l.amount, period_type=l.period_type.value if hasattr(l.period_type, "value") else str(l.period_type), category_id=l.category_id, threshold_warning=l.threshold_warning, status=l.status.value if hasattr(l.status, "value") else str(l.status)) for l in limits]


@router.get("/{limit_id}", response_model=LimitResponseSchema)
async def get_limit(limit_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_limit_repository(session)
    limit = await repo.find_by_id(limit_id)
    if not limit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Límite no encontrado")
    check_ownership(limit, current_user)
    return LimitResponseSchema(
        id=limit.id, user_id=limit.user_id, name=limit.name, amount=limit.amount,
        period_type=limit.period_type.value if hasattr(limit.period_type, "value") else str(limit.period_type),
        category_id=limit.category_id, threshold_warning=limit.threshold_warning,
        status=limit.status.value if hasattr(limit.status, "value") else str(limit.status),
    )


@router.put("/{limit_id}", response_model=LimitResponseSchema)
async def update_limit(limit_id: str, payload: UpdateLimitRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_limit_repository(session)
    limit = await repo.find_by_id(limit_id)
    if not limit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Límite no encontrado")
    check_ownership(limit, current_user)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(limit, field, value)

    await repo.save(limit)
    await session.commit()

    return LimitResponseSchema(
        id=limit.id, user_id=limit.user_id, name=limit.name, amount=limit.amount,
        period_type=limit.period_type.value if hasattr(limit.period_type, "value") else str(limit.period_type),
        category_id=limit.category_id, threshold_warning=limit.threshold_warning,
        status=limit.status.value if hasattr(limit.status, "value") else str(limit.status),
    )


@router.delete("/{limit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_limit(limit_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_limit_repository(session)
    limit = await repo.find_by_id(limit_id)
    if not limit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Límite no encontrado")
    check_ownership(limit, current_user)

    await repo.delete(limit_id)
    await session.commit()
