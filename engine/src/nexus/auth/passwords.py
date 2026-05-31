"""Hash e verificação de senha via bcrypt (direto, sem passlib).

bcrypt tem limite de 72 bytes na senha — o Pydantic schema limita o input
ao mesmo teto para evitar truncamento silencioso.
"""

from __future__ import annotations

import bcrypt

BCRYPT_MAX_BYTES = 72


def hash_password(plain: str) -> str:
    pwd = plain.encode("utf-8")
    if len(pwd) > BCRYPT_MAX_BYTES:
        raise ValueError(f"senha excede {BCRYPT_MAX_BYTES} bytes")
    return bcrypt.hashpw(pwd, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pwd = plain.encode("utf-8")[:BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(pwd, hashed.encode("utf-8"))
    except ValueError:
        return False
