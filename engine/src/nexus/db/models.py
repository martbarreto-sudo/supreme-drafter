"""Modelos de persistência do Nexus.

Para SQLite-compat (testes), usamos String(36) para UUID em vez do tipo nativo.
Tipos PostgreSQL específicos (JSONB, etc.) serão usados apenas quando entrarmos
em modelos que exigem (StripeEvent.payload, Audit.halt_violations) em fases futuras.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class OABStatus(str, enum.Enum):
    PENDING_DECLARATION = "PENDING_DECLARATION"  # signup feito, OAB ainda não declarada
    DECLARED = "DECLARED"                          # advogado declarou OAB + assinou TOS
    VERIFIED = "VERIFIED"                          # verificação manual/API confirmou
    REVOKED = "REVOKED"                            # acesso suspenso


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    oab_numero: Mapped[str] = mapped_column(String(10))
    oab_uf: Mapped[str] = mapped_column(String(2))
    oab_status: Mapped[OABStatus] = mapped_column(
        SAEnum(OABStatus, name="oabstatus"),
        default=OABStatus.PENDING_DECLARATION,
    )
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    tos_aceito_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
