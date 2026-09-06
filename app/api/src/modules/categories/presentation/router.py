from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_category_use_case, build_category_repository
from infrastructure.database.session import get_session
from modules.categories.presentation.schemas import CreateCategoryRequestSchema, CategoryResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CreateCategoryRequestSchema, session: AsyncSession = Depends(get_session)):
    use_case = build_create_category_use_case(session)
    try:
        input_dto = payload.to_input_dto()
        result = await use_case.execute(input_dto)
        await session.commit()
        return CategoryResponseSchema(id=result.id, user_id=result.user_id, name=result.name, type=result.type, parent_id=result.parent_id, status=result.status)
    except (ValidationError, ValueError) as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "VALIDATION_ERROR", "message": str(e)}) from e
    except ConflictError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": e.code, "message": e.message}) from e


@router.get("/user/{user_id}", response_model=list[CategoryResponseSchema])
async def list_categories_by_user(user_id: str, session: AsyncSession = Depends(get_session)):
    repo = build_category_repository(session)
    categories = await repo.find_by_user(user_id)
    return [CategoryResponseSchema(id=c.id, user_id=c.user_id, name=c.name, type=c.type.value if hasattr(c.type, "value") else str(c.type), parent_id=c.parent_id, status=c.status.value if hasattr(c.status, "value") else str(c.status)) for c in categories]
