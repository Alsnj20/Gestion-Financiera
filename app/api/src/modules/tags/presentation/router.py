from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_tag_use_case, build_tag_repository
from infrastructure.database.session import get_session
from modules.tags.presentation.schemas import CreateTagRequestSchema, TagResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("", response_model=TagResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_tag(payload: CreateTagRequestSchema, session: AsyncSession = Depends(get_session)):
    use_case = build_create_tag_use_case(session)
    try:
        input_dto = payload.to_input_dto()
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
async def list_tags_by_user(user_id: str, session: AsyncSession = Depends(get_session)):
    repo = build_tag_repository(session)
    tags = await repo.find_by_user(user_id)
    return [TagResponseSchema(id=t.id, user_id=t.user_id, name=t.name) for t in tags]
