from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_transaction_use_case, build_transaction_repository
from modules.auth.presentation.dependencies import get_current_user, check_ownership
from infrastructure.database.session import get_session
from modules.transactions.presentation.schemas import CreateTransactionRequestSchema, UpdateTransactionRequestSchema, TransactionResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: CreateTransactionRequestSchema,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    use_case = build_create_transaction_use_case(session)
    try:
        # Traduce Pydantic a DTO nativo antes de ejecutar la aplicación
        input_dto = payload.to_input_dto()
        input_dto.user_id = current_user["user_id"]
        result = await use_case.execute(input_dto)
        await session.commit()

        return TransactionResponseSchema(
            id=result.id,
            user_id=result.user_id,
            account_id=result.account_id,
            type=result.type,
            amount=result.amount,
            currency=result.currency,
            description=result.description,
            category_id=result.category_id,
            payment_method_id=result.payment_method_id,
            source=result.source,
            status=result.status,
            transaction_date=result.transaction_date,
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


@router.get("/{tx_id}", response_model=TransactionResponseSchema)
async def get_transaction(tx_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_transaction_repository(session)
    tx = await repo.find_by_id(tx_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    check_ownership(tx, current_user)

    return TransactionResponseSchema(
        id=tx.id,
        user_id=tx.user_id,
        account_id=tx.account_id,
        type=tx.type.value if hasattr(tx.type, "value") else str(tx.type),
        amount=tx.amount,
        currency=tx.currency,
        description=tx.description,
        category_id=tx.category_id,
        payment_method_id=tx.payment_method_id,
        source=tx.source.value if hasattr(tx.source, "value") else str(tx.source),
        status=tx.status.value if hasattr(tx.status, "value") else str(tx.status),
        transaction_date=tx.transaction_date,
    )


@router.get("/user/{user_id}", response_model=list[TransactionResponseSchema])
async def list_transactions_by_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    if user_id != current_user["user_id"] and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    repo = build_transaction_repository(session)
    transactions = await repo.list_by_user(user_id)

    return [
        TransactionResponseSchema(
            id=tx.id,
            user_id=tx.user_id,
            account_id=tx.account_id,
            type=tx.type.value if hasattr(tx.type, "value") else str(tx.type),
            amount=tx.amount,
            currency=tx.currency,
            description=tx.description,
            category_id=tx.category_id,
            payment_method_id=tx.payment_method_id,
            source=tx.source.value if hasattr(tx.source, "value") else str(tx.source),
            status=tx.status.value if hasattr(tx.status, "value") else str(tx.status),
            transaction_date=tx.transaction_date,
        )
        for tx in transactions
    ]


@router.put("/{tx_id}", response_model=TransactionResponseSchema)
async def update_transaction(tx_id: str, payload: UpdateTransactionRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_transaction_repository(session)
    tx = await repo.find_by_id(tx_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    check_ownership(tx, current_user)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(tx, field, value)

    await repo.save(tx)
    await session.commit()

    return TransactionResponseSchema(
        id=tx.id,
        user_id=tx.user_id,
        account_id=tx.account_id,
        type=tx.type.value if hasattr(tx.type, "value") else str(tx.type),
        amount=tx.amount,
        currency=tx.currency,
        description=tx.description,
        category_id=tx.category_id,
        payment_method_id=tx.payment_method_id,
        source=tx.source.value if hasattr(tx.source, "value") else str(tx.source),
        status=tx.status.value if hasattr(tx.status, "value") else str(tx.status),
        transaction_date=tx.transaction_date,
    )


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(tx_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_transaction_repository(session)
    tx = await repo.find_by_id(tx_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    check_ownership(tx, current_user)

    await repo.delete(tx_id)
    await session.commit()
