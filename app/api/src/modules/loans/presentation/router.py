from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_loan_use_case, build_loan_repository
from infrastructure.database.session import get_session
from modules.loans.presentation.schemas import CreateLoanRequestSchema, LoanResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("", response_model=LoanResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_loan(payload: CreateLoanRequestSchema, session: AsyncSession = Depends(get_session)):
    use_case = build_create_loan_use_case(session)
    try:
        input_dto = payload.to_input_dto()
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
async def list_loans_by_user(user_id: str, session: AsyncSession = Depends(get_session)):
    repo = build_loan_repository(session)
    loans = await repo.find_by_user(user_id)
    return [LoanResponseSchema(id=l.id, user_id=l.user_id, borrower_name=l.borrower_name, principal_amount=l.principal_amount, status=l.status.value if hasattr(l.status, "value") else str(l.status)) for l in loans]
