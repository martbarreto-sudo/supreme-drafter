"""Wrapper finíssimo sobre o SDK Stripe. Valida env vars na hora do uso.

Não configuramos `stripe.api_key` no import — fazemos em cada chamada que
precisa, lendo do env. Isto permite que testes mocquem ANTES do uso e que
o boot do app não falhe se STRIPE_SECRET_KEY estiver ausente (chave só é
necessária para os endpoints /billing/checkout e /billing/webhook).
"""

from __future__ import annotations

import os

import stripe


class StripeNaoConfigurado(Exception):
    """STRIPE_SECRET_KEY ou STRIPE_WEBHOOK_SECRET ausente."""


def _secret_key() -> str:
    key = os.getenv("STRIPE_SECRET_KEY")
    if not key:
        raise StripeNaoConfigurado("STRIPE_SECRET_KEY não configurado")
    return key


def webhook_secret() -> str:
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not secret:
        raise StripeNaoConfigurado("STRIPE_WEBHOOK_SECRET não configurado")
    return secret


def configure_for_call() -> None:
    """Chama isto antes de usar stripe.X.create() ou retrieve()."""
    stripe.api_key = _secret_key()
