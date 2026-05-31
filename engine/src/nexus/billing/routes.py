"""Rotas /billing — subscription (leitura), checkout (Stripe), webhook (Stripe)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from nexus.auth.deps import get_current_user
from nexus.db.models import User
from nexus.db.session import get_session

from .checkout import create_checkout_session
from .plans import PlanIndisponivel
from .schemas import CheckoutIn, CheckoutOut, SubscriptionOut
from .service import find_subscription
from .stripe_client import StripeNaoConfigurado
from .webhook import (
    WebhookPayloadInvalid,
    WebhookSignatureInvalid,
    process_webhook,
)

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


@router.post("/checkout", response_model=CheckoutOut)
async def checkout(
    payload: CheckoutIn,
    user: User = Depends(get_current_user),
) -> CheckoutOut:
    """Cria Stripe Checkout Session e devolve URL para redirect.

    Plan_code TRIAL é rejeitado (não vendável). Plano sem STRIPE_PRICE_X
    configurado → 503.
    """
    try:
        url = create_checkout_session(user, payload.plan_code)
    except PlanIndisponivel as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except StripeNaoConfigurado as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return CheckoutOut(url=url)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Recebe events do Stripe. Idempotente via StripeEvent.event_id.

    Requer body bruto (raw bytes) para validação de assinatura HMAC.
    Não usar response_model — devolvemos dict simples.
    """
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    try:
        result = await process_webhook(session, payload, signature)
    except WebhookSignatureInvalid as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    except WebhookPayloadInvalid as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    except StripeNaoConfigurado as exc:
        return JSONResponse(status_code=503, content={"error": str(exc)})
    return result
