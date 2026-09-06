from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_account_use_case, build_account_repository
from modules.auth.presentation.dependencies import get_current_user, check_ownership
from infrastructure.database.session import get_session
from modules.accounts.presentation.schemas import CreateAccountRequestSchema, UpdateAccountRequestSchema, AccountResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: CreateAccountRequestSchema,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    use_case = build_create_account_use_case(session)
    try:
        # Traduce Pydantic a DTO nativo antes de ejecutar la aplicación
        input_dto = payload.to_input_dto()
        input_dto.user_id = current_user["user_id"]
        result = await use_case.execute(input_dto)
        await session.commit()

        return AccountResponseSchema(
            id=result.id,
            user_id=result.user_id,
            name=result.name,
            type=result.type,
            currency=result.currency,
            initial_balance=result.initial_balance,
            current_balance=result.current_balance,
            is_default=result.is_default,
            status=result.status,
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


@router.get("/{account_id}", response_model=AccountResponseSchema)
async def get_account(account_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_account_repository(session)
    account = await repo.find_by_id(account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    check_ownership(account, current_user)

    return AccountResponseSchema(
        id=account.id,
        user_id=account.user_id,
        name=account.name,
        type=account.type.value if hasattr(account.type, "value") else str(account.type),
        currency=account.currency,
        initial_balance=account.initial_balance,
        current_balance=account.current_balance,
        is_default=account.is_default,
        status=account.status.value if hasattr(account.status, "value") else str(account.status),
    )


@router.get("/user/{user_id}", response_model=list[AccountResponseSchema])
async def list_accounts_by_user(user_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    if user_id != current_user["user_id"] and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    repo = build_account_repository(session)
    accounts = await repo.find_by_user(user_id)

    return [
        AccountResponseSchema(
            id=account.id,
            user_id=account.user_id,
            name=account.name,
            type=account.type.value if hasattr(account.type, "value") else str(account.type),
            currency=account.currency,
            initial_balance=account.initial_balance,
            current_balance=account.current_balance,
            is_default=account.is_default,
            status=account.status.value if hasattr(account.status, "value") else str(account.status),
        )
        for account in accounts
    ]


@router.put("/{account_id}", response_model=AccountResponseSchema)
async def update_account(account_id: str, payload: UpdateAccountRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_account_repository(session)
    account = await repo.find_by_id(account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    check_ownership(account, current_user)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(account, field, value)

    await repo.save(account)
    await session.commit()

    return AccountResponseSchema(
        id=account.id,
        user_id=account.user_id,
        name=account.name,
        type=account.type.value if hasattr(account.type, "value") else str(account.type),
        currency=account.currency,
        initial_balance=account.initial_balance,
        current_balance=account.current_balance,
        is_default=account.is_default,
        status=account.status.value if hasattr(account.status, "value") else str(account.status),
    )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_account_repository(session)
    account = await repo.find_by_id(account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    check_ownership(account, current_user)

    await repo.delete(account_id)
    await session.commit()
