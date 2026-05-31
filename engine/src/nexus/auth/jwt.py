"""JWT — geração e validação.

Sem fallback de secret hardcoded. JWT_SECRET ausente derruba boot/uso
deliberadamente — fallback "DEFAULT_SECRET" em código é vulnerabilidade
crítica (qualquer leitor do source forja tokens).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt

ALGORITHM = "HS256"
DEFAULT_TTL_MINUTES = 15


def _secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET não configurado")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET muito curto (mínimo 32 chars)")
    return secret


def _ttl_minutes() -> int:
    raw = os.getenv("JWT_TTL_MINUTES")
    return int(raw) if raw else DEFAULT_TTL_MINUTES


def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=_ttl_minutes())).timestamp()),
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Levanta jose.JWTError em token inválido ou expirado."""
    return jwt.decode(token, _secret(), algorithms=[ALGORITHM])
