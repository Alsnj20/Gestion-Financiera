"""OTP generation and verification utilities."""

from __future__ import annotations

import random
import string
from datetime import UTC, datetime, timedelta


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP code."""
    return "".join(random.choices(string.digits, k=length))


def get_otp_expiry(seconds: int = 300) -> datetime:
    """Get expiry datetime for OTP (segundos centralizados en settings)."""
    return datetime.now(UTC) + timedelta(seconds=seconds)


def is_otp_expired(expires_at: datetime) -> bool:
    """Check if OTP has expired."""
    return datetime.now(UTC) > expires_at
