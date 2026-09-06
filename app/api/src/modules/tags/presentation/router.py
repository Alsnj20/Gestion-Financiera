from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_tag_use_case, build_tag_repository
from modules.auth.presentation.dependencies import get_current_user, check_ownership
from infrastructure.database.session import get_session
from modules.tags.presentation.schemas import CreateTagRequestSchema, UpdateTagRequestSchema, TagResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("", response_model=TagResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_tag(payload: CreateTagRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    use_case = build_create_tag_use_case(session)
    try:
        input_dto = payload.to_input_dto()
        input_dto.user_id = current_user["user_id"]
        result = await use_case.execute(input_dto)
        await session.commit()
        return TagResponseSchema(id=result.id, user_id=result.user_id, name=result.name)
    except (ValidationError, ValueError) as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "VALIDATION_ERROR", "message": str(e)}) from e
    except ConflictError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": e.code, "message": e.message}) from e


@router.get("/user/{user_id}", response_model=list[TagResponseSchema])
async def list_tags_by_user(user_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    if user_id != current_user["user_id"] and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    repo = build_tag_repository(session)
    tags = await repo.find_by_user(user_id)
    return [TagResponseSchema(id=t.id, user_id=t.user_id, name=t.name) for t in tags]


@router.get("/{tag_id}", response_model=TagResponseSchema)
async def get_tag(tag_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_tag_repository(session)
    tag = await repo.find_by_id(tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag no encontrado")
    check_ownership(tag, current_user)
    return TagResponseSchema(id=tag.id, user_id=tag.user_id, name=tag.name)


@router.put("/{tag_id}", response_model=TagResponseSchema)
async def update_tag(tag_id: str, payload: UpdateTagRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_tag_repository(session)
    tag = await repo.find_by_id(tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag no encontrado")
    check_ownership(tag, current_user)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(tag, field, value)

    await repo.save(tag)
    await session.commit()

    return TagResponseSchema(id=tag.id, user_id=tag.user_id, name=tag.name)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_tag_repository(session)
    tag = await repo.find_by_id(tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag no encontrado")
    check_ownership(tag, current_user)

    await repo.delete(tag_id)
    await session.commit()
