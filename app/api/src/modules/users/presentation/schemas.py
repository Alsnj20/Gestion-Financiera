from __future__ import annotations

from pydantic import BaseModel, Field


class UserResponseSchema(BaseModel):
    id: str
    name: str
    phone: str
    email: str
    role: str = "USER"
    is_verified: bool = False
    timezone: str
    currency: str


class UpdateUserRequestSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    timezone: str | None = Field(default=None, max_length=64)
    currency: str | None = Field(default=None, max_length=10)
