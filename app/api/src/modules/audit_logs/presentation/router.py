from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_create_audit_log_use_case, build_audit_log_repository
from infrastructure.database.session import get_session
from modules.audit_logs.presentation.schemas import CreateAuditLogRequestSchema, AuditLogResponseSchema
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.post("", response_model=AuditLogResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_audit_log(payload: CreateAuditLogRequestSchema, session: AsyncSession = Depends(get_session)):
    use_case = build_create_audit_log_use_case(session)
    try:
        input_dto = payload.to_input_dto()
        result = await use_case.execute(input_dto)
        await session.commit()
        return AuditLogResponseSchema(
            id=result.id, user_id=result.user_id, entity_type=result.entity_type,
            entity_id=result.entity_id, action=result.action, source=result.source,
        )
    except (ValidationError, ValueError) as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "VALIDATION_ERROR", "message": str(e)}) from e
    except ConflictError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": e.code, "message": e.message}) from e


@router.get("/user/{user_id}", response_model=list[AuditLogResponseSchema])
async def list_audit_logs_by_user(user_id: str, session: AsyncSession = Depends(get_session)):
    repo = build_audit_log_repository(session)
    items = await repo.find_by_user(user_id)
    return [
        AuditLogResponseSchema(
            id=l.id, user_id=l.user_id, entity_type=l.entity_type,
            entity_id=l.entity_id, action=l.action, source=l.source,
        )
        for l in items
    ]
