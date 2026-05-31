"""Cria Stripe Checkout Session em modo subscription.

`client_reference_id` carrega o user.id da nossa base — o webhook usa esse
campo para amarrar a Subscription pago ao usuário correto. Sem isso, não
há como saber quem pagou.
"""

from __future__ import annotations

import os

import stripe

from nexus.db.models import PlanCode, User

from .plans import plan_config
from .stripe_client import configure_for_call


def _success_url() -> str:
    base = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return f"{base}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"


def _cancel_url() -> str:
    base = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return f"{base}/billing/cancel"


def create_checkout_session(user: User, plan_code: PlanCode) -> str:
    """Retorna a URL hosted do Stripe Checkout. Levanta PlanIndisponivel
    ou StripeNaoConfigurado se config faltando."""
    plan = plan_config(plan_code)
    configure_for_call()

    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
        client_reference_id=user.id,
        customer_email=user.email,
        success_url=_success_url(),
        cancel_url=_cancel_url(),
    )
    return session.url
