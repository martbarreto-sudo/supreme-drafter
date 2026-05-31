"""Auth Bearer simples para endpoints que processam PII.

Não substitui um sistema de identidade — é só uma trava para que /autos e /draft/llm
não fiquem abertos à internet em deploy. NEXUS_TOKEN configurado via secret.
"""

from __future__ import annotations

import os
import secrets

from fastapi import Header, HTTPException


def require_bearer(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv("NEXUS_TOKEN")
    if not expected:
        raise HTTPException(503, "NEXUS_TOKEN não configurado")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authorization Bearer ausente")
    token = authorization.removeprefix("Bearer ")
    if not secrets.compare_digest(token, expected):
        raise HTTPException(403, "Bearer inválido")
