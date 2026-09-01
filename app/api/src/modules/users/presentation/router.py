from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_user_use_case, build_user_repository
from infrastructure.database.session import get_session
from modules.users.presentation.schemas import CreateUserRequestSchema, UserResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: CreateUserRequestSchema,
    session: AsyncSession = Depends(get_session)
):
    use_case = build_create_user_use_case(session)
    try:
        # Traduce Pydantic a DTO nativo antes de ejecutar la aplicación
        input_dto = payload.to_input_dto()
        result = await use_case.execute(input_dto)
        await session.commit()

        return UserResponseSchema(
            id=result.id,
            name=result.name,
            phone=result.phone,
            email=result.email,
            timezone=result.timezone,
            currency=result.currency,
        )
    except (ValidationError, ValueError) as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": str(e)},
        ) from e
    except ConflictError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": e.code, "message": e.message},
        ) from e


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
        timezone=user.timezone,
        currency=user.currency,
    )
