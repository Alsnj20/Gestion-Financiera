from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from modules.tags.application.use_cases.create_tag import CreateTagInput


class CreateTagRequestSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=40)

    def to_input_dto(self) -> CreateTagInput:
        return CreateTagInput(user_id="", name=self.name)


class UpdateTagRequestSchema(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=40)


class TagResponseSchema(BaseModel):
    id: str
    user_id: str
    name: str
