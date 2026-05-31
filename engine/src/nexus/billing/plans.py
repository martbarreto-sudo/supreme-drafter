"""Mapeamento de planos ↔ Stripe price IDs.

Os IDs reais vêm do env (STRIPE_PRICE_SOLO/BANCA/CORPORATE). Em testes,
mocka via monkeypatch.setenv. Faltar em produção = checkout/webhook
falham explicitamente — não há fallback.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from nexus.db.models import PlanCode


@dataclass(frozen=True)
class PlanConfig:
    code: PlanCode
    stripe_price_id: str
    pecas_mensais: int


_PLAN_PECAS = {
    PlanCode.SOLO: 10,
    PlanCode.BANCA: 50,
    PlanCode.CORPORATE: 200,
}

_PLAN_ENV = {
    PlanCode.SOLO: "STRIPE_PRICE_SOLO",
    PlanCode.BANCA: "STRIPE_PRICE_BANCA",
    PlanCode.CORPORATE: "STRIPE_PRICE_CORPORATE",
}


class PlanIndisponivel(Exception):
    """Plano não configurado (STRIPE_PRICE_X ausente do env)."""


def plan_config(code: PlanCode) -> PlanConfig:
    if code == PlanCode.TRIAL:
        raise PlanIndisponivel("TRIAL não é vendável via Stripe")
    env_var = _PLAN_ENV[code]
    price_id = os.getenv(env_var)
    if not price_id:
        raise PlanIndisponivel(f"{env_var} não configurado")
    return PlanConfig(code=code, stripe_price_id=price_id, pecas_mensais=_PLAN_PECAS[code])


def plan_by_price_id(price_id: str) -> PlanConfig | None:
    """Reverse-lookup: dado um stripe_price_id, retorna o plano. None se desconhecido."""
    for code in (PlanCode.SOLO, PlanCode.BANCA, PlanCode.CORPORATE):
        env_var = _PLAN_ENV[code]
        if os.getenv(env_var) == price_id:
            return PlanConfig(
                code=code, stripe_price_id=price_id, pecas_mensais=_PLAN_PECAS[code]
            )
    return None
