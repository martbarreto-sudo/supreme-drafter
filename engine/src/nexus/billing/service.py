"""Regras de negócio de assinatura e cota.

Não conhece HTTP — recebe AsyncSession e levanta exceções de domínio
que a camada de rotas traduz em 402 com mensagens consistentes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nexus.db.models import PlanCode, Subscription, SubscriptionStatus, User

TRIAL_DURATION_DAYS = 14
TRIAL_PECAS = 3


class SemAssinatura(Exception):
    """Usuário não tem nenhuma assinatura cadastrada."""


class AssinaturaInativa(Exception):
    """Assinatura existe mas status é PAST_DUE ou CANCELED."""

    def __init__(self, status: SubscriptionStatus) -> None:
        super().__init__(status.value)
        self.status = status


class PeriodoExpirado(Exception):
    """Período da assinatura (trial ou ciclo pago) já passou."""


class QuotaExcedida(Exception):
    """pecas_consumidas_no_periodo >= pecas_incluidas."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_trial_subscription(user: User) -> Subscription:
    """Cria objeto Subscription em TRIAL. Quem persiste é o caller."""
    start = _now()
    return Subscription(
        user_id=user.id,
        plan_code=PlanCode.TRIAL,
        status=SubscriptionStatus.TRIAL,
        stripe_subscription_id=None,
        current_period_start=start,
        current_period_end=start + timedelta(days=TRIAL_DURATION_DAYS),
        pecas_incluidas=TRIAL_PECAS,
        pecas_consumidas_no_periodo=0,
    )


async def find_subscription(session: AsyncSession, user_id: str) -> Subscription | None:
    result = await session.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def assert_pode_consumir_peca(
    session: AsyncSession, user: User
) -> Subscription:
    sub = await find_subscription(session, user.id)
    if sub is None:
        raise SemAssinatura()
    if sub.status not in (SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE):
        raise AssinaturaInativa(sub.status)
    # current_period_end pode vir naive do SQLite — normaliza para UTC-aware
    period_end = sub.current_period_end
    if period_end.tzinfo is None:
        period_end = period_end.replace(tzinfo=timezone.utc)
    if period_end < _now():
        raise PeriodoExpirado()
    if sub.pecas_consumidas_no_periodo >= sub.pecas_incluidas:
        raise QuotaExcedida()
    return sub


async def consumir_peca(session: AsyncSession, sub: Subscription) -> None:
    """Incrementa contador de peças do ciclo. Caller controla quando chamar
    (depois de geração bem-sucedida, não antes)."""
    sub.pecas_consumidas_no_periodo += 1
    session.add(sub)
    await session.commit()
