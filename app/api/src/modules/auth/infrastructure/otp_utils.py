"""OTP generation and verification utilities."""
from __future__ import annotations

import random
import string
from datetime import datetime, timedelta, timezone


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP code."""
    return "".join(random.choices(string.digits, k=length))


def get_otp_expiry(minutes: int = 5) -> datetime:
    """Get expiry datetime for OTP."""
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


def is_otp_expired(expires_at: datetime) -> bool:
    """Check if OTP has expired."""
    return datetime.now(timezone.utc) > expires_at
