from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_loan_use_case, build_loan_repository
from modules.auth.presentation.dependencies import get_current_user, check_ownership
from infrastructure.database.session import get_session
from modules.loans.presentation.schemas import CreateLoanRequestSchema, UpdateLoanRequestSchema, LoanResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("", response_model=LoanResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_loan(payload: CreateLoanRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    use_case = build_create_loan_use_case(session)
    try:
        input_dto = payload.to_input_dto()
        input_dto.user_id = current_user["user_id"]
        result = await use_case.execute(input_dto)
        await session.commit()
        return LoanResponseSchema(id=result.id, user_id=result.user_id, borrower_name=result.borrower_name, principal_amount=result.principal_amount, status=result.status)
    except (ValidationError, ValueError) as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "VALIDATION_ERROR", "message": str(e)}) from e
    except ConflictError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": e.code, "message": e.message}) from e


@router.get("/user/{user_id}", response_model=list[LoanResponseSchema])
async def list_loans_by_user(user_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    if user_id != current_user["user_id"] and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    repo = build_loan_repository(session)
    loans = await repo.find_by_user(user_id)
    return [LoanResponseSchema(id=l.id, user_id=l.user_id, borrower_name=l.borrower_name, principal_amount=l.principal_amount, status=l.status.value if hasattr(l.status, "value") else str(l.status)) for l in loans]


@router.get("/{loan_id}", response_model=LoanResponseSchema)
async def get_loan(loan_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_loan_repository(session)
    loan = await repo.find_by_id(loan_id)
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Préstamo no encontrado")
    check_ownership(loan, current_user)
    return LoanResponseSchema(
        id=loan.id, user_id=loan.user_id, borrower_name=loan.borrower_name,
        principal_amount=loan.principal_amount,
        status=loan.status.value if hasattr(loan.status, "value") else str(loan.status),
    )


@router.put("/{loan_id}", response_model=LoanResponseSchema)
async def update_loan(loan_id: str, payload: UpdateLoanRequestSchema, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_loan_repository(session)
    loan = await repo.find_by_id(loan_id)
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Préstamo no encontrado")
    check_ownership(loan, current_user)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(loan, field, value)

    await repo.save(loan)
    await session.commit()

    return LoanResponseSchema(
        id=loan.id, user_id=loan.user_id, borrower_name=loan.borrower_name,
        principal_amount=loan.principal_amount,
        status=loan.status.value if hasattr(loan.status, "value") else str(loan.status),
    )


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_loan(loan_id: str, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    repo = build_loan_repository(session)
    loan = await repo.find_by_id(loan_id)
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Préstamo no encontrado")
    check_ownership(loan, current_user)

    await repo.delete(loan_id)
    await session.commit()
