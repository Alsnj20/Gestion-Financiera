"""WhatsApp linking token utilities."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta


def generate_link_token() -> str:
    """Generate a secure random token for WhatsApp linking."""
    return secrets.token_urlsafe(32)


def get_link_token_expiry(hours: int = 24) -> datetime:
    """Get expiry datetime for link token."""
    return datetime.now(UTC) + timedelta(hours=hours)
