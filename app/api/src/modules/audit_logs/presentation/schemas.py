from pydantic import BaseModel, Field
from modules.audit_logs.application.use_cases.create_audit_log import CreateAuditLogInput


class CreateAuditLogRequestSchema(BaseModel):
    entity_type: str = Field(..., min_length=1, max_length=40)
    entity_id: str = Field(..., min_length=1, max_length=80)
    action: str = Field(..., min_length=1, max_length=20)
    old_value: dict | None = None
    new_value: dict | None = None
    source: str = Field(default="MANUAL", max_length=20)

    def to_input_dto(self) -> CreateAuditLogInput:
        return CreateAuditLogInput(
            user_id="",
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            action=self.action,
            old_value=self.old_value,
            new_value=self.new_value,
            source=self.source,
        )


class AuditLogResponseSchema(BaseModel):
    id: str
    user_id: str
    entity_type: str
    entity_id: str
    action: str
    source: str
