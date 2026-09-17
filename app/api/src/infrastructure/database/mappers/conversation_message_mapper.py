"""Shim de compatibilidad — la fuente vive en el módulo conversations."""
from __future__ import annotations

from modules.conversations.infrastructure.mappers.conversation_message_mapper import (
    to_domain,
    to_model,
)

__all__ = ["to_domain", "to_model"]
