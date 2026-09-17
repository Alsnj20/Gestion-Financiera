from __future__ import annotations

from dataclasses import dataclass

from modules.audit_logs.application.dtos import (
    CreateAuditLogOutput,
    to_audit_log_output,
)
from modules.audit_logs.application.ports.audit_log_repository import (
    AuditLogRepositoryPort,
)
from modules.audit_logs.domain.entities.audit_log import AuditLog


@dataclass(frozen=True, slots=True)
class CreateAuditLogInput:
    user_id: str
    entity_type: str
    entity_id: str
    action: str
    old_value: dict | None = None
    new_value: dict | None = None
    source: str = "MANUAL"


class CreateAuditLogUseCase:
    def __init__(self, repo: AuditLogRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: CreateAuditLogInput) -> CreateAuditLogOutput:
        log = AuditLog.create(
            user_id=inp.user_id,
            entity_type=inp.entity_type,
            entity_id=inp.entity_id,
            action=inp.action,
            old_value=inp.old_value,
            new_value=inp.new_value,
            source=inp.source,
        )
        await self._repo.save(log)

        return to_audit_log_output(log)
