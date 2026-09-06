"""Auth schemas for login, register, and token refresh."""
from pydantic import BaseModel, EmailStr, Field


class LoginRequestSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class RegisterRequestSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    phone: str = Field(..., min_length=7, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    timezone: str = Field(default="America/Lima", max_length=64)
    currency: str = Field(default="PEN", max_length=10)


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class RefreshRequestSchema(BaseModel):
    refresh_token: str


class RefreshResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
