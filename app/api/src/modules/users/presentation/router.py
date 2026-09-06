from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_user_repository
from infrastructure.database.session import get_session
from modules.auth.presentation.dependencies import (
    get_current_user,
    check_ownership,
    require_admin,
)
from modules.users.presentation.schemas import UserResponseSchema

router = APIRouter(prefix="/users", tags=["users"])


def _to_response(user) -> UserResponseSchema:
    return UserResponseSchema(
        id=user.id, name=user.name, phone=user.phone, email=user.email,
        role=user.role, is_verified=user.is_verified,
        timezone=user.timezone, currency=user.currency,
    )


@router.get("", response_model=list[UserResponseSchema])
async def list_users(
    current_user: dict = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Directorio de usuarios: solo admin (solo lectura)."""
    repo = build_user_repository(session)
    users = await repo.list_all()
    return [_to_response(u) for u in users]


class UpdateUserRequestSchema(BaseModel):
    name: str = Field(default=None, min_length=1, max_length=120)
    email: str = Field(default=None, max_length=255)
    timezone: str = Field(default=None, max_length=64)
    currency: str = Field(default=None, max_length=10)


@router.get("/{user_id}", response_model=UserResponseSchema)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    repo = build_user_repository(session)
    user = await repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    check_ownership(user, current_user)

    return UserResponseSchema(
        id=user.id, name=user.name, phone=user.phone, email=user.email,
        role=user.role, is_verified=user.is_verified,
        timezone=user.timezone, currency=user.currency,
    )


@router.put("/{user_id}", response_model=UserResponseSchema)
async def update_user(
    user_id: str,
    payload: UpdateUserRequestSchema,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    repo = build_user_repository(session)
    user = await repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    check_ownership(user, current_user)

    updated = user.update_profile(
        name=payload.name,
        email=payload.email,
        timezone=payload.timezone,
        currency=payload.currency,
    )
    await repo.save(updated)
    await session.commit()

    return UserResponseSchema(
        id=updated.id, name=updated.name, phone=updated.phone, email=updated.email,
        role=updated.role, is_verified=updated.is_verified,
        timezone=updated.timezone, currency=updated.currency,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Borrado total (CASCADE): solo admin, vía solicitud GDPR."""
    repo = build_user_repository(session)
    user = await repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    await repo.delete(user_id)
    await session.commit()
