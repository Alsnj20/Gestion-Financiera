from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from modules.notifications.application.use_cases.create_notification import (
    CreateNotificationInput,
)


class CreateNotificationRequestSchema(BaseModel):
    type: str = Field(default="GENERAL", max_length=40)
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=1000)
    scheduled_at: datetime | None = None
    related_entity_type: str = Field(default="", max_length=40)
    related_entity_id: str = Field(default="", max_length=80)

    def to_input_dto(self, user_id: str) -> CreateNotificationInput:
        return CreateNotificationInput(
            user_id=user_id,
            type=self.type,
            title=self.title,
            message=self.message,
            scheduled_at=self.scheduled_at,
            related_entity_type=self.related_entity_type,
            related_entity_id=self.related_entity_id,
        )


class UpdateNotificationRequestSchema(BaseModel):
    """Solo metadatos: el status cambia por send/cancel."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    message: str | None = Field(default=None, min_length=1, max_length=1000)
    scheduled_at: datetime | None = None


class NotificationResponseSchema(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    message: str
    scheduled_at: datetime
    sent_at: datetime | None = None
    status: str
