"""Auth router with login, register, refresh, and logout endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.session import get_session
from modules.auth.infrastructure.jwt_utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from modules.auth.presentation.schemas import (
    LoginRequestSchema,
    RegisterRequestSchema,
    TokenResponseSchema,
    RefreshRequestSchema,
    RefreshResponseSchema,
)
from modules.users.infrastructure.adapters.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from modules.users.application.use_cases.create_user import CreateUserUseCase, CreateUserInput
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponseSchema, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequestSchema, session: AsyncSession = Depends(get_session)):
    user_repo = SqlAlchemyUserRepository(session)
    use_case = CreateUserUseCase(user_repo)
    try:
        input_dto = CreateUserInput(
            name=payload.name,
            phone=payload.phone,
            email=payload.email,
            password=payload.password,
            timezone=payload.timezone,
            currency=payload.currency,
        )
        result = await use_case.execute(input_dto)
        await session.commit()

        access_token = create_access_token(result.id, result.email)
        refresh_token = create_refresh_token(result.id, result.email)

        return TokenResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=result.id,
            email=result.email,
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


@router.post("/login", response_model=TokenResponseSchema)
async def login(payload: LoginRequestSchema, session: AsyncSession = Depends(get_session)):
    import bcrypt

    user_repo = SqlAlchemyUserRepository(session)
    user = await user_repo.find_by_email(payload.email.lower().strip())

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Email o contraseña incorrectos"},
        )

    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Email o contraseña incorrectos"},
        )

    if not bcrypt.checkpw(payload.password.encode("utf-8"), user.password_hash.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Email o contraseña incorrectos"},
        )

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id, user.email)

    return TokenResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        email=user.email,
    )


@router.post("/refresh", response_model=RefreshResponseSchema)
async def refresh_token(payload: RefreshRequestSchema, session: AsyncSession = Depends(get_session)):
    token_data = decode_token(payload.refresh_token)

    if not token_data or token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token de refresco inválido o expirado"},
        )

    user_id = token_data.get("sub")
    email = token_data.get("email")

    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token de refresco inválido"},
        )

    user_repo = SqlAlchemyUserRepository(session)
    user = await user_repo.find_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "Usuario no encontrado"},
        )

    access_token = create_access_token(user.id, user.email)

    return RefreshResponseSchema(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    """Logout is client-side: delete tokens from storage.
    This endpoint exists for API completeness."""
    return None
