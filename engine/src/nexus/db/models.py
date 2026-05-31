"""Modelos de persistência do Nexus.

Para SQLite-compat (testes), usamos String(36) para UUID em vez do tipo nativo.
Tipos PostgreSQL específicos (JSONB, etc.) serão usados apenas quando entrarmos
em modelos que exigem (StripeEvent.payload, Audit.halt_violations) em fases futuras.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class OABStatus(str, enum.Enum):
    PENDING_DECLARATION = "PENDING_DECLARATION"  # signup feito, OAB ainda não declarada
    DECLARED = "DECLARED"                          # advogado declarou OAB + assinou TOS
    VERIFIED = "VERIFIED"                          # verificação manual/API confirmou
    REVOKED = "REVOKED"                            # acesso suspenso


class SubscriptionStatus(str, enum.Enum):
    TRIAL = "TRIAL"          # 14 dias após signup, 3 peças
    ACTIVE = "ACTIVE"        # Stripe subscription paga e em dia
    PAST_DUE = "PAST_DUE"    # pagamento falhou; bloqueia uso até regularizar
    CANCELED = "CANCELED"    # cancelado; sem novos ciclos


class PlanCode(str, enum.Enum):
    TRIAL = "TRIAL"
    SOLO = "SOLO"
    BANCA = "BANCA"
    CORPORATE = "CORPORATE"


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


class Subscription(Base):
    """Uma assinatura por usuário (1:1). Upgrade/downgrade atualiza a mesma row.

    Trial é criado automaticamente no signup. Mudanças de plano (Fase C/Stripe)
    atualizam plan_code + status + stripe_subscription_id + período.
    """

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), unique=True, index=True
    )
    plan_code: Mapped[PlanCode] = mapped_column(SAEnum(PlanCode, name="plancode"))
    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus, name="subscriptionstatus")
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True
    )
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    pecas_incluidas: Mapped[int] = mapped_column(Integer)
    pecas_consumidas_no_periodo: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PaymentStatus(str, enum.Enum):
    PAID = "PAID"
    REFUNDED = "REFUNDED"
    FAILED = "FAILED"


class Payment(Base):
    """Cada invoice paga vira uma Payment. Audit trail financeiro."""

    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True
    )
    stripe_invoice_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="brl")
    status: Mapped[PaymentStatus] = mapped_column(SAEnum(PaymentStatus, name="paymentstatus"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class StripeEvent(Base):
    """Idempotência de webhook. event_id da Stripe é PK natural.

    Antes de aplicar mutações de qualquer event_type, checa se event_id já
    está aqui. Se sim, retorna 200 sem fazer nada. Esta é a primitiva
    correta de idempotência (não checar Payment como blueprint externo
    sugeria — racy + tarde demais no fluxo).
    """

    __tablename__ = "stripe_events"

    event_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100))
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
