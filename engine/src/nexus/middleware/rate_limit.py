"""Rate limiting via slowapi.

Estratégia por endpoint (decorators aplicados em cada route):
- /auth/login: 5/min — frear brute-force de senha
- /auth/signup: 3/min — frear criação de contas em massa
- /draft/llm: 30/min — proteção de custo LLM e abuso
- /autos: 60/min — uploads em rajada
- /billing/checkout: 10/min

Key função: IP de origem (X-Forwarded-For respeitado pelo slowapi via
get_remote_address). Pode-se trocar por per-user key no futuro lendo o
sub do JWT em uma key_func custom.

Desabilitação em tests via env NEXUS_RATE_LIMIT_DISABLED=1 (conftest seta).
"""

from __future__ import annotations

import os

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


def _enabled() -> bool:
    return os.getenv("NEXUS_RATE_LIMIT_DISABLED") != "1"


limiter = Limiter(key_func=get_remote_address, enabled=_enabled())


def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit excedido",
            "detail": str(exc.detail),
            "retry_after_seconds": 60,
        },
        headers={"Retry-After": "60"},
    )
