from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_user_repository
from infrastructure.database.session import get_session
from modules.users.presentation.schemas import UserResponseSchema

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=UserResponseSchema)
async def get_user(user_id: str, session: AsyncSession = Depends(get_session)):
    repo = build_user_repository(session)
    user = await repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    return UserResponseSchema(
        id=user.id,
        name=user.name,
        phone=user.phone,
        email=user.email,
        role=user.role,
        is_verified=user.is_verified,
        timezone=user.timezone,
        currency=user.currency,
    )
