"""Testes de Subscription/trial.

Cobrem: criação automática no signup, leitura via /billing/subscription,
exceções de domínio (sem assinatura, inativa, expirada, quota excedida)
e o happy path de consumir_peca.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from nexus.billing.service import (
    AssinaturaInativa,
    PeriodoExpirado,
    QuotaExcedida,
    SemAssinatura,
    TRIAL_DURATION_DAYS,
    TRIAL_PECAS,
    assert_pode_consumir_peca,
    consumir_peca,
    find_subscription,
)
from nexus.db.models import (
    PlanCode,
    Subscription,
    SubscriptionStatus,
    User,
)


_SIGNUP = {
    "email": "trial@tigre.org",
    "name": "Trial User",
    "oab_numero": "12345",
    "oab_uf": "PE",
    "password": "senhaSegura12345",
}


async def _signup_and_token(client) -> tuple[str, str]:
    sr = client.post("/auth/signup", json=_SIGNUP)
    user_id = sr.json()["id"]
    lr = client.post(
        "/auth/login",
        json={"email": _SIGNUP["email"], "password": _SIGNUP["password"]},
    )
    return user_id, lr.json()["access_token"]


# ---------- criação automática no signup ----------


async def test_signup_cria_subscription_trial(client, db_session):
    user_id, _ = await _signup_and_token(client)
    sub = await find_subscription(db_session, user_id)
    assert sub is not None
    assert sub.plan_code == PlanCode.TRIAL
    assert sub.status == SubscriptionStatus.TRIAL
    assert sub.pecas_incluidas == TRIAL_PECAS
    assert sub.pecas_consumidas_no_periodo == 0
    assert sub.stripe_subscription_id is None


async def test_trial_period_dura_14_dias(client, db_session):
    user_id, _ = await _signup_and_token(client)
    sub = await find_subscription(db_session, user_id)
    duracao = sub.current_period_end - sub.current_period_start
    # tolerância de 1 segundo para arredondamento
    assert abs(duracao - timedelta(days=TRIAL_DURATION_DAYS)) < timedelta(seconds=1)


# ---------- GET /billing/subscription ----------


async def test_get_subscription_sem_token_401(client):
    r = client.get("/billing/subscription")
    assert r.status_code == 401


async def test_get_subscription_retorna_trial_recem_criado(client):
    _, token = await _signup_and_token(client)
    r = client.get(
        "/billing/subscription", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["plan_code"] == "TRIAL"
    assert body["status"] == "TRIAL"
    assert body["pecas_incluidas"] == TRIAL_PECAS
    assert body["pecas_consumidas_no_periodo"] == 0
    assert body["pecas_restantes"] == TRIAL_PECAS


# ---------- assert_pode_consumir_peca ----------


async def test_assert_sem_assinatura_levanta(db_session):
    """Usuário sem Subscription levanta SemAssinatura."""
    user = User(
        email="solo@x.com", name="Solo", oab_numero="111", oab_uf="PE",
        password_hash="x",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    with pytest.raises(SemAssinatura):
        await assert_pode_consumir_peca(db_session, user)


async def test_assert_assinatura_canceled_levanta(client, db_session):
    user_id, _ = await _signup_and_token(client)
    sub = await find_subscription(db_session, user_id)
    sub.status = SubscriptionStatus.CANCELED
    await db_session.commit()
    user = await db_session.get(User, user_id)
    with pytest.raises(AssinaturaInativa) as exc:
        await assert_pode_consumir_peca(db_session, user)
    assert exc.value.status == SubscriptionStatus.CANCELED


async def test_assert_periodo_expirado_levanta(client, db_session):
    user_id, _ = await _signup_and_token(client)
    sub = await find_subscription(db_session, user_id)
    sub.current_period_end = datetime.now(timezone.utc) - timedelta(seconds=1)
    await db_session.commit()
    user = await db_session.get(User, user_id)
    with pytest.raises(PeriodoExpirado):
        await assert_pode_consumir_peca(db_session, user)


async def test_assert_quota_esgotada_levanta(client, db_session):
    user_id, _ = await _signup_and_token(client)
    sub = await find_subscription(db_session, user_id)
    sub.pecas_consumidas_no_periodo = sub.pecas_incluidas
    await db_session.commit()
    user = await db_session.get(User, user_id)
    with pytest.raises(QuotaExcedida):
        await assert_pode_consumir_peca(db_session, user)


async def test_assert_happy_path_retorna_subscription(client, db_session):
    user_id, _ = await _signup_and_token(client)
    user = await db_session.get(User, user_id)
    sub = await assert_pode_consumir_peca(db_session, user)
    assert sub.user_id == user_id
    assert sub.pecas_consumidas_no_periodo == 0


# ---------- consumir_peca ----------


async def test_consumir_peca_incrementa_contador(client, db_session):
    user_id, _ = await _signup_and_token(client)
    user = await db_session.get(User, user_id)
    sub = await assert_pode_consumir_peca(db_session, user)

    await consumir_peca(db_session, sub)
    await db_session.refresh(sub)
    assert sub.pecas_consumidas_no_periodo == 1

    await consumir_peca(db_session, sub)
    await db_session.refresh(sub)
    assert sub.pecas_consumidas_no_periodo == 2


async def test_consumir_peca_esgota_trial(client, db_session):
    """Consumir TRIAL_PECAS peças → próxima chamada falha com QuotaExcedida."""
    user_id, _ = await _signup_and_token(client)
    user = await db_session.get(User, user_id)
    sub = await assert_pode_consumir_peca(db_session, user)

    for _ in range(TRIAL_PECAS):
        await consumir_peca(db_session, sub)

    # após consumir todas as peças, próxima validação falha
    fresh = await db_session.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    sub_after = fresh.scalar_one()
    assert sub_after.pecas_consumidas_no_periodo == TRIAL_PECAS
    with pytest.raises(QuotaExcedida):
        await assert_pode_consumir_peca(db_session, user)
