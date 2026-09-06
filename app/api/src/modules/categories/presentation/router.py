from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_category_use_case, build_category_repository
from modules.auth.presentation.dependencies import get_current_user, check_ownership
from infrastructure.database.session import get_session
from modules.categories.presentation.schemas import CreateCategoryRequestSchema, UpdateCategoryRequestSchema, CategoryResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CreateCategoryRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    use_case = build_create_category_use_case(session)
    try:
        input_dto = payload.to_input_dto()
        input_dto.user_id = current_user["user_id"]
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
async def list_categories_by_user(user_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    if user_id != current_user["user_id"] and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    repo = build_category_repository(session)
    categories = await repo.find_by_user(user_id)
    return [CategoryResponseSchema(id=c.id, user_id=c.user_id, name=c.name, type=c.type.value if hasattr(c.type, "value") else str(c.type), parent_id=c.parent_id, status=c.status.value if hasattr(c.status, "value") else str(c.status)) for c in categories]


@router.get("/{category_id}", response_model=CategoryResponseSchema)
async def get_category(category_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_category_repository(session)
    category = await repo.find_by_id(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    check_ownership(category, current_user)
    return CategoryResponseSchema(
        id=category.id,
        user_id=category.user_id,
        name=category.name,
        type=category.type.value if hasattr(category.type, "value") else str(category.type),
        parent_id=category.parent_id,
        status=category.status.value if hasattr(category.status, "value") else str(category.status),
    )


@router.put("/{category_id}", response_model=CategoryResponseSchema)
async def update_category(category_id: str, payload: UpdateCategoryRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_category_repository(session)
    category = await repo.find_by_id(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    check_ownership(category, current_user)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(category, field, value)

    await repo.save(category)
    await session.commit()

    return CategoryResponseSchema(
        id=category.id,
        user_id=category.user_id,
        name=category.name,
        type=category.type.value if hasattr(category.type, "value") else str(category.type),
        parent_id=category.parent_id,
        status=category.status.value if hasattr(category.status, "value") else str(category.status),
    )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_category_repository(session)
    category = await repo.find_by_id(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    check_ownership(category, current_user)

    await repo.delete(category_id)
    await session.commit()
