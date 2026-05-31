"""Testes do POST /billing/checkout — JWT obrigatório, mocka Stripe SDK."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import signup_and_login


def _wire_stripe_env(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake_for_unit_tests")
    monkeypatch.setenv("STRIPE_PRICE_SOLO", "price_solo_test_123")
    monkeypatch.setenv("STRIPE_PRICE_BANCA", "price_banca_test_456")
    monkeypatch.setenv("FRONTEND_URL", "https://app.example.com")


async def test_checkout_sem_jwt_401(client):
    r = client.post("/billing/checkout", json={"plan_code": "SOLO"})
    assert r.status_code == 401


async def test_checkout_plan_trial_503(client, monkeypatch):
    """TRIAL não é vendável via Stripe — escopo §2 e §4.1."""
    _wire_stripe_env(monkeypatch)
    _, token = signup_and_login(client)
    r = client.post(
        "/billing/checkout",
        headers={"Authorization": f"Bearer {token}"},
        json={"plan_code": "TRIAL"},
    )
    assert r.status_code == 503


async def test_checkout_plan_sem_env_503(client, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.delenv("STRIPE_PRICE_CORPORATE", raising=False)
    _, token = signup_and_login(client)
    r = client.post(
        "/billing/checkout",
        headers={"Authorization": f"Bearer {token}"},
        json={"plan_code": "CORPORATE"},
    )
    assert r.status_code == 503


async def test_checkout_sem_secret_key_503(client, monkeypatch):
    monkeypatch.setenv("STRIPE_PRICE_SOLO", "price_solo_test_123")
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    _, token = signup_and_login(client)
    r = client.post(
        "/billing/checkout",
        headers={"Authorization": f"Bearer {token}"},
        json={"plan_code": "SOLO"},
    )
    assert r.status_code == 503


async def test_checkout_solo_devolve_url(client, monkeypatch):
    _wire_stripe_env(monkeypatch)
    user, token = signup_and_login(client)

    fake_session = MagicMock()
    fake_session.url = "https://checkout.stripe.com/c/pay/cs_test_fake"

    with patch("nexus.billing.checkout.stripe.checkout.Session.create", return_value=fake_session) as create_mock:
        r = client.post(
            "/billing/checkout",
            headers={"Authorization": f"Bearer {token}"},
            json={"plan_code": "SOLO"},
        )

    assert r.status_code == 200
    assert r.json()["url"] == "https://checkout.stripe.com/c/pay/cs_test_fake"

    # Valida que os parâmetros corretos chegaram à Stripe
    kwargs = create_mock.call_args.kwargs
    assert kwargs["mode"] == "subscription"
    assert kwargs["client_reference_id"] == user["id"]
    assert kwargs["customer_email"] == user["email"]
    assert kwargs["line_items"] == [{"price": "price_solo_test_123", "quantity": 1}]
    assert "session_id={CHECKOUT_SESSION_ID}" in kwargs["success_url"]
    assert "https://app.example.com" in kwargs["success_url"]


async def test_checkout_plano_invalido_422(client, monkeypatch):
    _wire_stripe_env(monkeypatch)
    _, token = signup_and_login(client)
    r = client.post(
        "/billing/checkout",
        headers={"Authorization": f"Bearer {token}"},
        json={"plan_code": "INVENTADO"},
    )
    assert r.status_code == 422
