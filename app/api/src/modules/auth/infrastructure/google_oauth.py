"""Google OAuth token verification using Google's official libraries."""

from __future__ import annotations

import os
from dataclasses import dataclass

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


@dataclass(frozen=True, slots=True)
class GoogleUserInfo:
    google_id: str
    email: str
    name: str
    email_verified: bool


def verify_google_token(id_token_str: str) -> GoogleUserInfo | None:
    """
    Verify Google ID token using Google's official library.
    This verifies the signature, expiry, and audience.
    NEVER trust the token without verification.
    """
    if not GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID not configured")

    try:
        # This verifies:
        # 1. Token signature (cryptographic verification)
        # 2. Token expiry
        # 3. Audience (our client ID)
        # 4. Issuer (accounts.google.com)
        idinfo = id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )

        # Only accept emails from Google's verified accounts
        email_verified = idinfo.get("email_verified", False)
        if not email_verified:
            return None

        return GoogleUserInfo(
            google_id=idinfo.get("sub", ""),
            email=idinfo.get("email", ""),
            name=idinfo.get("name", ""),
            email_verified=email_verified,
        )
    except Exception:
        return None
