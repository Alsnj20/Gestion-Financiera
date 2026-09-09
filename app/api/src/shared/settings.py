"""Configuración centralizada (pydantic-settings).

Toda la lógica de producción lee sus parámetros de aquí: sin valores
mágicos en use cases ni routers. Development puede usar valores cómodos
vía variables de entorno sin tocar reglas de negocio.

Valores objetivo de producción = defaults de este archivo.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"

    # ---- JWT (D2): vida corta, validación criptográfica siempre ----
    JWT_SECRET_KEY: str = "gestion-financiera-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # objetivo prod: 15 min
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---- OTP (D8): expiración, intentos y rate limit configurables ----
    OTP_EXPIRATION_SECONDS: int = 300
    OTP_MAX_ATTEMPTS: int = 5
    OTP_RATE_LIMIT_COUNT: int = 3
    OTP_RATE_LIMIT_WINDOW_MINUTES: int = 10
    # "log" = DevelopmentOtpSender (DEBUG controlado), "none" = sin proveedor
    # (prod rechaza el envío hasta configurar WhatsApp/SMTP real).
    OTP_SENDER: str | None = None

    # ---- WhatsApp linking ----
    LINK_TOKEN_EXPIRATION_HOURS: int = 24

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def otp_sender_name(self) -> str:
        """Resolución del provider sin tocar use cases (D8)."""
        if self.OTP_SENDER:
            return self.OTP_SENDER
        return "none" if self.is_production else "log"

    @property
    def link_token_expiration_seconds(self) -> int:
        return self.LINK_TOKEN_EXPIRATION_HOURS * 3600


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
