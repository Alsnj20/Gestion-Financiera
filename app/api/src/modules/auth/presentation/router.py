"""Auth router — Solo Google OAuth + OTP + WhatsApp linking."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from composition import get_auth_controller
from modules.auth.application.use_cases.generate_link_token import (
    GenerateLinkTokenInput,
)
from modules.auth.application.use_cases.google_auth import GoogleAuthInput
from modules.auth.application.use_cases.link_whatsapp import LinkWhatsAppInput
from modules.auth.application.use_cases.logout import LogoutInput
from modules.auth.application.use_cases.refresh_token import RefreshTokenInput
from modules.auth.application.use_cases.request_otp import RequestOtpInput
from modules.auth.application.use_cases.validate_link_token import (
    ValidateLinkTokenInput,
)
from modules.auth.application.use_cases.verify_user import VerifyUserInput
from modules.auth.presentation.controllers.auth_controller import AuthController
from modules.auth.presentation.schemas import (
    GenerateLinkTokenRequestSchema,
    GoogleAuthRequestSchema,
    LinkTokenResponseSchema,
    LinkWhatsAppRequestSchema,
    OtpResponseSchema,
    RefreshRequestSchema,
    RefreshResponseSchema,
    ResendOtpRequestSchema,
    SendOtpRequestSchema,
    TokenResponseSchema,
    ValidateLinkTokenRequestSchema,
    VerifyOtpRequestSchema,
)
from shared.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])

AuthCtrl = Annotated[AuthController, Depends(get_auth_controller)]


# ==================== GOOGLE OAUTH (UPSERT) ====================


@router.post("/google", response_model=TokenResponseSchema)
async def google_auth(payload: GoogleAuthRequestSchema, controller: AuthCtrl):
    """
    Autenticación con Google OAuth (Upsert).

    - Email viene SOLO del token verificado de Google, NUNCA del body.
    - Si el usuario ya existe (por email): retorna tokens (login).
    - Si no existe: crea cuenta automáticamente con phone opcional (register).
    """
    result = await controller.google_auth(
        GoogleAuthInput(
            id_token=payload.id_token,
            phone=payload.phone,
            timezone=payload.timezone,
            currency=payload.currency,
        )
    )
    return TokenResponseSchema(**result)


# ==================== OTP VERIFICATION ====================


@router.post("/send-otp", response_model=OtpResponseSchema)
async def send_otp(payload: SendOtpRequestSchema, controller: AuthCtrl):
    """Respuesta genérica anti-enumeración (D6): igual exista o no el número."""
    await controller.request_otp(
        RequestOtpInput(phone=payload.phone, channel=payload.channel)
    )

    return OtpResponseSchema(
        message="Si el número está registrado, recibirás un código",
        channel=payload.channel,
        expires_in=settings.OTP_EXPIRATION_SECONDS,
    )


@router.post("/verify-otp")
async def verify_otp(payload: VerifyOtpRequestSchema, controller: AuthCtrl):
    """Verify OTP code."""
    await controller.verify_user(
        VerifyUserInput(phone=payload.phone, code=payload.code, channel=payload.channel)
    )

    return {"message": "Cuenta verificada exitosamente", "verified": True}


@router.post("/resend-otp", response_model=OtpResponseSchema)
async def resend_otp(payload: ResendOtpRequestSchema, controller: AuthCtrl):
    """Resend OTP code (mismo flujo y contrato genérico que send-otp)."""
    await controller.request_otp(
        RequestOtpInput(phone=payload.phone, channel=payload.channel)
    )

    return OtpResponseSchema(
        message="Si el número está registrado, recibirás un código",
        channel=payload.channel,
        expires_in=settings.OTP_EXPIRATION_SECONDS,
    )


# ==================== WHATSAPP LINKING ====================


@router.post("/whatsapp/generate-token", response_model=LinkTokenResponseSchema)
async def generate_whatsapp_link_token(
    payload: GenerateLinkTokenRequestSchema,
    controller: AuthCtrl,
):
    """Generate a token for WhatsApp bot linking."""
    result = await controller.generate_link_token(
        GenerateLinkTokenInput(phone_number=payload.phone)
    )

    return LinkTokenResponseSchema(
        token=result["token"],
        wa_link=result["wa_link"],
        expires_in=settings.link_token_expiration_seconds,
    )


@router.post("/whatsapp/validate-token")
async def validate_whatsapp_link_token(
    payload: ValidateLinkTokenRequestSchema,
    controller: AuthCtrl,
):
    """Validate a WhatsApp link token (called from bot or web)."""
    result = await controller.validate_link_token(
        ValidateLinkTokenInput(token=payload.token)
    )

    return {"valid": True, "phone_number": result["phone_number"]}


@router.post("/whatsapp/link")
async def link_whatsapp(
    payload: LinkWhatsAppRequestSchema,
    controller: AuthCtrl,
):
    """Link WhatsApp token to user account (el usuario debe existir)."""
    await controller.link_whatsapp(
        LinkWhatsAppInput(token=payload.token, user_id=payload.user_id)
    )

    return {"message": "WhatsApp vinculado exitosamente", "linked": True}


# ==================== TOKEN MANAGEMENT ====================


@router.post("/refresh", response_model=RefreshResponseSchema)
async def refresh_token(payload: RefreshRequestSchema, controller: AuthCtrl):
    result = await controller.refresh(
        RefreshTokenInput(refresh_token=payload.refresh_token)
    )

    return RefreshResponseSchema(
        access_token=result["access_token"], refresh_token=result["refresh_token"]
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequestSchema, controller: AuthCtrl):
    """Revoca la sesión refresh (D3). Idempotente."""
    await controller.logout(LogoutInput(refresh_token=payload.refresh_token))
