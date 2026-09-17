from __future__ import annotations

from pydantic import BaseModel, Field


class CreateTagRequestSchema(BaseModel):
    name: str = Field(min_length=1, max_length=40)


class UpdateTagRequestSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=40)


class TagResponseSchema(BaseModel):
    id: str
    user_id: str
    name: str
