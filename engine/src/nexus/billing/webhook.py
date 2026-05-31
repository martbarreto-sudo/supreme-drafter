"""Processamento idempotente de webhooks Stripe.

Fluxo:
1. Validar assinatura via stripe.Webhook.construct_event (levanta em fraude)
2. Checar StripeEvent.event_id — se existe, no-op (retornou 200 antes)
3. Dispatch por event.type para handler específico
4. Gravar StripeEvent ANTES do commit final — qualquer retry recebe o
   no-op no passo 2

Eventos tratados:
- checkout.session.completed → ativa Subscription (trial → ACTIVE)
- invoice.payment_succeeded → renova período + reseta contador
- invoice.payment_failed → marca PAST_DUE
- customer.subscription.deleted → CANCELED

Eventos não-conhecidos: registramos StripeEvent (idempotente) e ignoramos
o payload. Isso evita reprocessar em retry mesmo se ainda não tratamos.
"""

from __future__ import annotations

from datetime import datetime, timezone

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nexus.db.models import (
    Payment,
    PaymentStatus,
    PlanCode,
    StripeEvent,
    Subscription,
    SubscriptionStatus,
    User,
)

from .plans import plan_by_price_id
from .stripe_client import configure_for_call, webhook_secret


class WebhookSignatureInvalid(Exception):
    pass


class WebhookPayloadInvalid(Exception):
    pass


def _parse_event(payload: bytes, signature: str | None) -> stripe.Event:
    if not signature:
        raise WebhookSignatureInvalid("Stripe-Signature header ausente")
    try:
        return stripe.Webhook.construct_event(payload, signature, webhook_secret())
    except stripe.error.SignatureVerificationError as exc:
        raise WebhookSignatureInvalid(str(exc)) from exc
    except ValueError as exc:
        raise WebhookPayloadInvalid(str(exc)) from exc


async def _ja_processado(session: AsyncSession, event_id: str) -> bool:
    result = await session.execute(
        select(StripeEvent).where(StripeEvent.event_id == event_id)
    )
    return result.scalar_one_or_none() is not None


def _to_utc(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


async def _find_user(session: AsyncSession, user_id: str) -> User | None:
    return await session.get(User, user_id)


async def _find_sub(session: AsyncSession, user_id: str) -> Subscription | None:
    result = await session.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def _find_sub_by_stripe_id(
    session: AsyncSession, stripe_sub_id: str
) -> Subscription | None:
    result = await session.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_sub_id
        )
    )
    return result.scalar_one_or_none()


# --- handlers por event.type ---


async def _handle_checkout_completed(session: AsyncSession, event: dict) -> None:
    obj = event["data"]["object"]
    user_id = obj.get("client_reference_id")
    stripe_sub_id = obj.get("subscription")
    if not user_id or not stripe_sub_id:
        return  # evento incompleto — ignora (idempotência já registra)

    user = await _find_user(session, user_id)
    if user is None:
        return

    # Recupera a subscription com line_items expandido para descobrir o plano
    configure_for_call()
    stripe_sub = stripe.Subscription.retrieve(stripe_sub_id, expand=["items.data.price"])
    items = stripe_sub.get("items", {}).get("data", [])
    if not items:
        return
    price_id = items[0].get("price", {}).get("id")
    plan = plan_by_price_id(price_id) if price_id else None
    if plan is None:
        return  # plano desconhecido — log e abort

    sub = await _find_sub(session, user_id)
    if sub is None:
        return  # signup deveria ter criado trial; defensivo
    sub.plan_code = plan.code
    sub.status = SubscriptionStatus.ACTIVE
    sub.stripe_subscription_id = stripe_sub_id
    sub.current_period_start = _to_utc(stripe_sub["current_period_start"])
    sub.current_period_end = _to_utc(stripe_sub["current_period_end"])
    sub.pecas_incluidas = plan.pecas_mensais
    sub.pecas_consumidas_no_periodo = 0
    session.add(sub)


async def _handle_invoice_paid(session: AsyncSession, event: dict) -> None:
    obj = event["data"]["object"]
    invoice_id = obj.get("id")
    stripe_sub_id = obj.get("subscription")
    amount = obj.get("amount_paid", 0)
    currency = (obj.get("currency") or "brl").lower()
    if not invoice_id or not stripe_sub_id:
        return

    sub = await _find_sub_by_stripe_id(session, stripe_sub_id)
    if sub is None:
        return

    # Atualiza período (renovação mensal) + reset contador
    lines = obj.get("lines", {}).get("data", [])
    period = lines[0].get("period") if lines else None
    if period:
        sub.current_period_start = _to_utc(period["start"])
        sub.current_period_end = _to_utc(period["end"])
    sub.pecas_consumidas_no_periodo = 0
    sub.status = SubscriptionStatus.ACTIVE
    session.add(sub)

    # Registra Payment (unique stripe_invoice_id — segunda entrega quebra
    # antes do commit, idempotência via StripeEvent já bloqueou)
    payment = Payment(
        user_id=sub.user_id,
        stripe_invoice_id=invoice_id,
        amount_cents=amount,
        currency=currency,
        status=PaymentStatus.PAID,
    )
    session.add(payment)


async def _handle_invoice_failed(session: AsyncSession, event: dict) -> None:
    obj = event["data"]["object"]
    stripe_sub_id = obj.get("subscription")
    invoice_id = obj.get("id")
    if not stripe_sub_id:
        return

    sub = await _find_sub_by_stripe_id(session, stripe_sub_id)
    if sub is None:
        return
    sub.status = SubscriptionStatus.PAST_DUE
    session.add(sub)

    if invoice_id:
        payment = Payment(
            user_id=sub.user_id,
            stripe_invoice_id=invoice_id,
            amount_cents=obj.get("amount_due", 0),
            currency=(obj.get("currency") or "brl").lower(),
            status=PaymentStatus.FAILED,
        )
        session.add(payment)


async def _handle_subscription_deleted(session: AsyncSession, event: dict) -> None:
    obj = event["data"]["object"]
    stripe_sub_id = obj.get("id")
    if not stripe_sub_id:
        return
    sub = await _find_sub_by_stripe_id(session, stripe_sub_id)
    if sub is None:
        return
    sub.status = SubscriptionStatus.CANCELED
    sub.plan_code = PlanCode.TRIAL  # downgrade simbólico; sem novas peças
    sub.pecas_incluidas = 0
    session.add(sub)


_HANDLERS = {
    "checkout.session.completed": _handle_checkout_completed,
    "invoice.payment_succeeded": _handle_invoice_paid,
    "invoice.payment_failed": _handle_invoice_failed,
    "customer.subscription.deleted": _handle_subscription_deleted,
}


async def process_webhook(
    session: AsyncSession, payload: bytes, signature: str | None
) -> dict:
    event = _parse_event(payload, signature)
    event_id = event["id"]

    if await _ja_processado(session, event_id):
        return {"status": "duplicate", "event_id": event_id}

    handler = _HANDLERS.get(event["type"])
    if handler is not None:
        await handler(session, event)

    session.add(StripeEvent(event_id=event_id, event_type=event["type"]))
    await session.commit()
    return {"status": "ok", "event_id": event_id, "event_type": event["type"]}
