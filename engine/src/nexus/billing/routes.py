"""Rotas /billing — por enquanto só leitura. Stripe checkout/webhook vêm na Fase C."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from nexus.auth.deps import get_current_user
from nexus.db.models import User
from nexus.db.session import get_session

from .schemas import SubscriptionOut
from .service import find_subscription

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/subscription", response_model=SubscriptionOut)
async def get_subscription(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SubscriptionOut:
    sub = await find_subscription(session, user.id)
    if sub is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sem assinatura cadastrada")
    return SubscriptionOut(
        plan_code=sub.plan_code.value,
        status=sub.status.value,
        current_period_start=sub.current_period_start,
        current_period_end=sub.current_period_end,
        pecas_incluidas=sub.pecas_incluidas,
        pecas_consumidas_no_periodo=sub.pecas_consumidas_no_periodo,
        pecas_restantes=max(0, sub.pecas_incluidas - sub.pecas_consumidas_no_periodo),
    )
