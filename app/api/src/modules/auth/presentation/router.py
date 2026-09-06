"""Auth router — Solo Google OAuth + OTP + WhatsApp linking."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.session import get_session
from modules.auth.infrastructure.jwt_utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from modules.auth.infrastructure.google_oauth import verify_google_token
from modules.auth.infrastructure.adapters.sqlalchemy_otp_repository import SqlAlchemyOtpRepository
from modules.auth.infrastructure.adapters.sqlalchemy_whatsapp_link_repository import SqlAlchemyWhatsAppLinkRepository
from modules.auth.application.use_cases.send_otp import SendOtpUseCase, SendOtpInput
from modules.auth.application.use_cases.verify_otp import VerifyOtpUseCase, VerifyOtpInput
from modules.auth.application.use_cases.generate_link_token import GenerateLinkTokenUseCase, GenerateLinkTokenInput
from modules.auth.application.use_cases.validate_link_token import ValidateLinkTokenUseCase, ValidateLinkTokenInput
from modules.auth.application.use_cases.link_whatsapp import LinkWhatsAppUseCase, LinkWhatsAppInput
from modules.auth.presentation.schemas import (
    GoogleAuthRequestSchema,
    SendOtpRequestSchema,
    VerifyOtpRequestSchema,
    ResendOtpRequestSchema,
    GenerateLinkTokenRequestSchema,
    ValidateLinkTokenRequestSchema,
    LinkWhatsAppRequestSchema,
    TokenResponseSchema,
    RefreshRequestSchema,
    RefreshResponseSchema,
    OtpResponseSchema,
    LinkTokenResponseSchema,
)
from modules.users.infrastructure.adapters.sqlalchemy_user_repository import SqlAlchemyUserRepository
from shared.errors import ConflictError, ValidationError

router = APIRouter(prefix="/auth", tags=["auth"])


# ==================== GOOGLE OAUTH (UPSERT) ====================

@router.post("/google", response_model=TokenResponseSchema)
async def google_auth(payload: GoogleAuthRequestSchema, session: AsyncSession = Depends(get_session)):
    """
    Autenticación con Google OAuth (Upsert).
    
    - Email viene SOLO del token verificado de Google, NUNCA del body.
    - Si el usuario ya existe (por email): retorna tokens (login).
    - Si no existe: crea cuenta automáticamente con phone opcional (register).
    """
    # 1. Verificar token con Google (firma + expiry + audience + email_verified)
    google_user = verify_google_token(payload.id_token)

    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_GOOGLE_TOKEN", "message": "Token de Google inválido o expirado"},
        )

    user_repo = SqlAlchemyUserRepository(session)
    is_new_user = False

    # 2. Buscar usuario existente por email (email viene del token VERIFICADO)
    existing_user = await user_repo.find_by_email(google_user.email)

    if existing_user:
        # LOGIN: Usuario ya existe
        user = existing_user
    else:
        # REGISTER: Crear nuevo usuario
        if not payload.phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "PHONE_REQUIRED", "message": "Teléfono requerido para nuevo registro"},
            )

        # Verificar que el teléfono no esté en uso
        phone_exists = await user_repo.find_by_phone(payload.phone)
        if phone_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "USER_PHONE_TAKEN", "message": f"Teléfono ya registrado: {payload.phone}"},
            )

        # Crear usuario con datos de Google + phone
        from modules.users.domain.entities.user import User
        user = User.create(
            name=google_user.name,
            phone=payload.phone,
            email=google_user.email,  # Email del token verificado
            google_id=google_user.google_id,
            is_verified=True,  # Google ya verificó el email
            timezone=payload.timezone,
            currency=payload.currency,
        )
        await user_repo.save(user)
        is_new_user = True

    # 3. Generar tokens
    access_token = create_access_token(user.id, user.email, user.role, user.is_verified)
    refresh_token = create_refresh_token(user.id, user.email)

    await session.commit()

    return TokenResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        email=user.email,
        role=user.role,
        is_verified=user.is_verified,
        is_new_user=is_new_user,
    )


# ==================== OTP VERIFICATION ====================

@router.post("/send-otp", response_model=OtpResponseSchema)
async def send_otp(payload: SendOtpRequestSchema, session: AsyncSession = Depends(get_session)):
    """Send OTP code via WhatsApp or Email."""
    user_repo = SqlAlchemyUserRepository(session)
    user = await user_repo.find_by_phone(payload.phone)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "Usuario no encontrado"},
        )

    otp_repo = SqlAlchemyOtpRepository(session)
    use_case = SendOtpUseCase(otp_repo)

    try:
        result = await use_case.execute(SendOtpInput(user_id=user.id, channel=payload.channel))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "RATE_LIMITED", "message": str(e)},
        ) from e

    # TODO: Send OTP via WhatsApp API or Email SMTP
    print(f"OTP Code for {payload.phone}: {result.code}")

    await session.commit()

    return OtpResponseSchema(
        message=f"Código enviado por {payload.channel}",
        channel=payload.channel,
        expires_in=300,
    )


@router.post("/verify-otp")
async def verify_otp(payload: VerifyOtpRequestSchema, session: AsyncSession = Depends(get_session)):
    """Verify OTP code."""
    user_repo = SqlAlchemyUserRepository(session)
    user = await user_repo.find_by_phone(payload.phone)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "Usuario no encontrado"},
        )

    otp_repo = SqlAlchemyOtpRepository(session)
    use_case = VerifyOtpUseCase(otp_repo)

    try:
        await use_case.execute(VerifyOtpInput(user_id=user.id, code=payload.code, channel=payload.channel))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "OTP_INVALID", "message": str(e)},
        ) from e

    verified_user = user.verify()
    await user_repo.save(verified_user)
    await session.commit()

    return {"message": "Cuenta verificada exitosamente", "verified": True}


@router.post("/resend-otp", response_model=OtpResponseSchema)
async def resend_otp(payload: ResendOtpRequestSchema, session: AsyncSession = Depends(get_session)):
    """Resend OTP code."""
    user_repo = SqlAlchemyUserRepository(session)
    user = await user_repo.find_by_phone(payload.phone)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "Usuario no encontrado"},
        )

    otp_repo = SqlAlchemyOtpRepository(session)
    use_case = SendOtpUseCase(otp_repo)

    try:
        result = await use_case.execute(SendOtpInput(user_id=user.id, channel=payload.channel))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "RATE_LIMITED", "message": str(e)},
        ) from e

    print(f"OTP Code for {payload.phone}: {result.code}")

    await session.commit()

    return OtpResponseSchema(
        message=f"Código reenviado por {payload.channel}",
        channel=payload.channel,
        expires_in=300,
    )


# ==================== WHATSAPP LINKING ====================

@router.post("/whatsapp/generate-token", response_model=LinkTokenResponseSchema)
async def generate_whatsapp_link_token(
    payload: GenerateLinkTokenRequestSchema,
    session: AsyncSession = Depends(get_session),
):
    """Generate a token for WhatsApp bot linking."""
    link_repo = SqlAlchemyWhatsAppLinkRepository(session)
    use_case = GenerateLinkTokenUseCase(link_repo)

    result = await use_case.execute(GenerateLinkTokenInput(phone_number=payload.phone))
    await session.commit()

    return LinkTokenResponseSchema(
        token=result.token,
        wa_link=result.wa_link,
        expires_in=86400,
    )


@router.post("/whatsapp/validate-token")
async def validate_whatsapp_link_token(
    payload: ValidateLinkTokenRequestSchema,
    session: AsyncSession = Depends(get_session),
):
    """Validate a WhatsApp link token (called from bot or web)."""
    link_repo = SqlAlchemyWhatsAppLinkRepository(session)
    use_case = ValidateLinkTokenUseCase(link_repo)

    result = await use_case.execute(ValidateLinkTokenInput(token=payload.token))

    if not result.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_TOKEN",
                "message": "Token inválido o expirado" if not result.already_linked else "Token ya utilizado",
            },
        )

    return {"valid": True, "phone_number": result.phone_number}


@router.post("/whatsapp/link")
async def link_whatsapp(
    payload: LinkWhatsAppRequestSchema,
    session: AsyncSession = Depends(get_session),
):
    """Link WhatsApp token to user account."""
    link_repo = SqlAlchemyWhatsAppLinkRepository(session)
    use_case = LinkWhatsAppUseCase(link_repo)

    try:
        await use_case.execute(LinkWhatsAppInput(token=payload.token, user_id=payload.user_id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "LINK_FAILED", "message": str(e)},
        ) from e

    await session.commit()

    return {"message": "WhatsApp vinculado exitosamente", "linked": True}


# ==================== TOKEN MANAGEMENT ====================

@router.post("/refresh", response_model=RefreshResponseSchema)
async def refresh_token(payload: RefreshRequestSchema, session: AsyncSession = Depends(get_session)):
    token_data = decode_token(payload.refresh_token)

    if not token_data or token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token de refresco inválido o expirado"},
        )

    user_id = token_data.get("sub")
    email = token_data.get("email")

    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token de refresco inválido"},
        )

    user_repo = SqlAlchemyUserRepository(session)
    user = await user_repo.find_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "Usuario no encontrado"},
        )

    access_token = create_access_token(user.id, user.email, user.role, user.is_verified)

    return RefreshResponseSchema(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    """Logout is client-side: delete tokens from storage."""
    return None
