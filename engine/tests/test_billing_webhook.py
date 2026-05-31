"""Testes do POST /billing/webhook — idempotência, assinatura, 4 event types.

Mocka `stripe.Webhook.construct_event` para evitar HMAC real. Cada teste
constrói um dict no formato do payload da Stripe e injeta via mock.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import stripe
from sqlalchemy import select

from nexus.billing.service import find_subscription
from nexus.db.models import (
    Payment,
    PaymentStatus,
    PlanCode,
    StripeEvent,
    SubscriptionStatus,
)
from tests.conftest import signup_and_login


def _wire_stripe_env(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test_fake")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("STRIPE_PRICE_SOLO", "price_solo_test_123")
    monkeypatch.setenv("STRIPE_PRICE_BANCA", "price_banca_test_456")


def _patch_construct_event(event_dict):
    """Faz stripe.Webhook.construct_event devolver o dict fornecido."""
    return patch(
        "nexus.billing.webhook.stripe.Webhook.construct_event",
        return_value=event_dict,
    )


# ---------- assinatura e payload ----------


async def test_webhook_sem_signature_400(client, monkeypatch):
    _wire_stripe_env(monkeypatch)
    r = client.post("/billing/webhook", content=b'{"fake": true}')
    assert r.status_code == 400


async def test_webhook_signature_invalida_400(client, monkeypatch):
    _wire_stripe_env(monkeypatch)
    err = stripe.error.SignatureVerificationError("invalid", "sig")
    with patch(
        "nexus.billing.webhook.stripe.Webhook.construct_event", side_effect=err
    ):
        r = client.post(
            "/billing/webhook",
            content=b"{}",
            headers={"Stripe-Signature": "wrong"},
        )
    assert r.status_code == 400


async def test_webhook_sem_env_secret_503(client, monkeypatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    r = client.post(
        "/billing/webhook",
        content=b"{}",
        headers={"Stripe-Signature": "sig"},
    )
    assert r.status_code == 503


# ---------- idempotência ----------


async def test_webhook_evento_duplicado_no_op(client, monkeypatch, db_session):
    _wire_stripe_env(monkeypatch)
    user, _ = signup_and_login(client)

    event = {
        "id": "evt_dup_123",
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": "sub_anything"}},
    }

    # Primeira entrega
    with _patch_construct_event(event):
        r1 = client.post(
            "/billing/webhook", content=b"{}", headers={"Stripe-Signature": "sig"}
        )
    assert r1.status_code == 200
    assert r1.json()["status"] == "ok"

    # Segunda entrega do MESMO evento — deve ser no-op
    with _patch_construct_event(event):
        r2 = client.post(
            "/billing/webhook", content=b"{}", headers={"Stripe-Signature": "sig"}
        )
    assert r2.status_code == 200
    assert r2.json()["status"] == "duplicate"

    # Apenas 1 StripeEvent gravado
    rows = await db_session.execute(
        select(StripeEvent).where(StripeEvent.event_id == "evt_dup_123")
    )
    assert len(list(rows.scalars())) == 1


# ---------- checkout.session.completed ----------


async def test_webhook_checkout_completed_ativa_subscription(
    client, monkeypatch, db_session
):
    _wire_stripe_env(monkeypatch)
    user, _ = signup_and_login(client)

    event = {
        "id": "evt_checkout_1",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": user["id"],
                "subscription": "sub_test_solo_001",
            }
        },
    }

    # Mock do stripe.Subscription.retrieve com line_items expandidos.
    # Dict puro funciona porque o webhook acessa via .get() e __getitem__.
    period_start = int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())
    period_end = int(datetime(2026, 7, 1, tzinfo=timezone.utc).timestamp())
    fake_stripe_sub = {
        "items": {"data": [{"price": {"id": "price_solo_test_123"}}]},
        "current_period_start": period_start,
        "current_period_end": period_end,
    }

    with _patch_construct_event(event), patch(
        "nexus.billing.webhook.stripe.Subscription.retrieve",
        return_value=fake_stripe_sub,
    ):
        r = client.post(
            "/billing/webhook", content=b"{}", headers={"Stripe-Signature": "sig"}
        )
    assert r.status_code == 200

    sub = await find_subscription(db_session, user["id"])
    assert sub.plan_code == PlanCode.SOLO
    assert sub.status == SubscriptionStatus.ACTIVE
    assert sub.stripe_subscription_id == "sub_test_solo_001"
    assert sub.pecas_incluidas == 10  # plan SOLO = 10 peças
    assert sub.pecas_consumidas_no_periodo == 0


async def test_webhook_checkout_plano_desconhecido_no_op(
    client, monkeypatch, db_session
):
    """Stripe envia price_id que não está nas nossas env vars → ignorado."""
    _wire_stripe_env(monkeypatch)
    user, _ = signup_and_login(client)

    event = {
        "id": "evt_unknown_price",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": user["id"],
                "subscription": "sub_xxx",
            }
        },
    }
    fake_stripe_sub = {
        "items": {"data": [{"price": {"id": "price_que_nao_existe"}}]},
        "current_period_start": 1700000000,
        "current_period_end": 1700000000,
    }
    with _patch_construct_event(event), patch(
        "nexus.billing.webhook.stripe.Subscription.retrieve",
        return_value=fake_stripe_sub,
    ):
        r = client.post(
            "/billing/webhook", content=b"{}", headers={"Stripe-Signature": "sig"}
        )
    assert r.status_code == 200
    # subscription continua em TRIAL — não foi promovida
    sub = await find_subscription(db_session, user["id"])
    assert sub.status == SubscriptionStatus.TRIAL


# ---------- invoice.payment_succeeded (renovação) ----------


async def test_webhook_invoice_paid_renova_periodo(client, monkeypatch, db_session):
    _wire_stripe_env(monkeypatch)
    user, _ = signup_and_login(client)

    # Pré-condição: usuário já está ACTIVE pós-checkout
    sub = await find_subscription(db_session, user["id"])
    sub.status = SubscriptionStatus.ACTIVE
    sub.plan_code = PlanCode.SOLO
    sub.stripe_subscription_id = "sub_test_solo_001"
    sub.pecas_incluidas = 10
    sub.pecas_consumidas_no_periodo = 7  # consumiu 7 no ciclo anterior
    await db_session.commit()

    new_start = int(datetime(2026, 7, 1, tzinfo=timezone.utc).timestamp())
    new_end = int(datetime(2026, 8, 1, tzinfo=timezone.utc).timestamp())

    event = {
        "id": "evt_invoice_1",
        "type": "invoice.payment_succeeded",
        "data": {
            "object": {
                "id": "in_test_001",
                "subscription": "sub_test_solo_001",
                "amount_paid": 39900,
                "currency": "brl",
                "lines": {
                    "data": [{"period": {"start": new_start, "end": new_end}}]
                },
            }
        },
    }

    with _patch_construct_event(event):
        r = client.post(
            "/billing/webhook", content=b"{}", headers={"Stripe-Signature": "sig"}
        )
    assert r.status_code == 200

    sub_after = await find_subscription(db_session, user["id"])
    assert sub_after.pecas_consumidas_no_periodo == 0  # ciclo resetou
    assert sub_after.status == SubscriptionStatus.ACTIVE

    # Payment criado
    pay_rows = await db_session.execute(
        select(Payment).where(Payment.stripe_invoice_id == "in_test_001")
    )
    payment = pay_rows.scalar_one()
    assert payment.amount_cents == 39900
    assert payment.status == PaymentStatus.PAID
    assert payment.user_id == user["id"]


# ---------- invoice.payment_failed (PAST_DUE) ----------


async def test_webhook_invoice_failed_marca_past_due(client, monkeypatch, db_session):
    _wire_stripe_env(monkeypatch)
    user, _ = signup_and_login(client)

    sub = await find_subscription(db_session, user["id"])
    sub.status = SubscriptionStatus.ACTIVE
    sub.stripe_subscription_id = "sub_active_001"
    await db_session.commit()

    event = {
        "id": "evt_invoice_failed_1",
        "type": "invoice.payment_failed",
        "data": {
            "object": {
                "id": "in_failed_001",
                "subscription": "sub_active_001",
                "amount_due": 39900,
                "currency": "brl",
            }
        },
    }

    with _patch_construct_event(event):
        r = client.post(
            "/billing/webhook", content=b"{}", headers={"Stripe-Signature": "sig"}
        )
    assert r.status_code == 200

    sub_after = await find_subscription(db_session, user["id"])
    assert sub_after.status == SubscriptionStatus.PAST_DUE


# ---------- customer.subscription.deleted (CANCELED) ----------


async def test_webhook_subscription_deleted_cancela(client, monkeypatch, db_session):
    _wire_stripe_env(monkeypatch)
    user, _ = signup_and_login(client)

    sub = await find_subscription(db_session, user["id"])
    sub.status = SubscriptionStatus.ACTIVE
    sub.plan_code = PlanCode.SOLO
    sub.stripe_subscription_id = "sub_to_cancel_001"
    sub.pecas_incluidas = 10
    await db_session.commit()

    event = {
        "id": "evt_cancel_1",
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": "sub_to_cancel_001"}},
    }

    with _patch_construct_event(event):
        r = client.post(
            "/billing/webhook", content=b"{}", headers={"Stripe-Signature": "sig"}
        )
    assert r.status_code == 200

    sub_after = await find_subscription(db_session, user["id"])
    assert sub_after.status == SubscriptionStatus.CANCELED
    assert sub_after.pecas_incluidas == 0


# ---------- eventos desconhecidos ainda registram para idempotência ----------


async def test_webhook_evento_desconhecido_grava_para_idempotencia(
    client, monkeypatch, db_session
):
    _wire_stripe_env(monkeypatch)
    event = {
        "id": "evt_unhandled_1",
        "type": "charge.dispute.created",
        "data": {"object": {}},
    }
    with _patch_construct_event(event):
        r = client.post(
            "/billing/webhook", content=b"{}", headers={"Stripe-Signature": "sig"}
        )
    assert r.status_code == 200
    # Mesmo sem handler, o event_id foi registrado (idempotência preserva)
    rows = await db_session.execute(
        select(StripeEvent).where(StripeEvent.event_id == "evt_unhandled_1")
    )
    assert rows.scalar_one() is not None
