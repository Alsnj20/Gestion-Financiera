"""Auth schemas for Google OAuth, OTP, and WhatsApp linking."""
from pydantic import BaseModel, Field


# ---- Google OAuth (solo campo requerido es id_token) ----
class GoogleAuthRequestSchema(BaseModel):
    """Email viene SOLO del token verificado de Google, nunca del body."""
    id_token: str = Field(..., min_length=10)
    phone: str = Field(default="", max_length=20)
    timezone: str = Field(default="America/Lima", max_length=64)
    currency: str = Field(default="PEN", max_length=10)


# ---- OTP Verification ----
class SendOtpRequestSchema(BaseModel):
    phone: str = Field(..., min_length=7, max_length=20)
    channel: str = Field(default="WHATSAPP", pattern="^(WHATSAPP|EMAIL)$")


class VerifyOtpRequestSchema(BaseModel):
    phone: str = Field(..., min_length=7, max_length=20)
    code: str = Field(..., min_length=6, max_length=6)
    channel: str = Field(default="WHATSAPP", pattern="^(WHATSAPP|EMAIL)$")


class ResendOtpRequestSchema(BaseModel):
    phone: str = Field(..., min_length=7, max_length=20)
    channel: str = Field(default="WHATSAPP", pattern="^(WHATSAPP|EMAIL)$")


# ---- WhatsApp Linking ----
class GenerateLinkTokenRequestSchema(BaseModel):
    phone: str = Field(..., min_length=7, max_length=20)


class ValidateLinkTokenRequestSchema(BaseModel):
    token: str = Field(..., min_length=10)


class LinkWhatsAppRequestSchema(BaseModel):
    token: str = Field(..., min_length=10)
    user_id: str = Field(..., min_length=1)


# ---- Token Response ----
class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str = "USER"
    is_verified: bool = False
    is_new_user: bool = False


class RefreshRequestSchema(BaseModel):
    refresh_token: str


class RefreshResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OtpResponseSchema(BaseModel):
    message: str
    channel: str
    expires_in: int = 300


class LinkTokenResponseSchema(BaseModel):
    token: str
    wa_link: str
    expires_in: int = 86400
