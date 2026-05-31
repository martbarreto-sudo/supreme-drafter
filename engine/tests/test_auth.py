"""Testes dos endpoints /auth.

Estratégia: override do dependency get_session para reusar a sessão
SQLite in-memory do fixture db_session. JWT_SECRET via monkeypatch.
"""

from __future__ import annotations

import pytest
from jose import JWTError


_VALID_SIGNUP = {
    "email": "marcelo@tigre.org",
    "name": "Marcelo Tigre",
    "oab_numero": "27543",
    "oab_uf": "PE",
    "password": "minhaSenhaForte123",
}


async def test_signup_cria_user(client):
    r = client.post("/auth/signup", json=_VALID_SIGNUP)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "marcelo@tigre.org"
    assert body["oab_status"] == "PENDING_DECLARATION"
    assert body["oab_uf"] == "PE"
    assert "password" not in body
    assert "password_hash" not in body


async def test_signup_email_duplicado_409(client):
    assert client.post("/auth/signup", json=_VALID_SIGNUP).status_code == 201
    assert client.post("/auth/signup", json=_VALID_SIGNUP).status_code == 409


async def test_signup_email_normalizado_lowercase(client):
    payload = {**_VALID_SIGNUP, "email": "Marcelo@TIGRE.org"}
    r = client.post("/auth/signup", json=payload)
    assert r.status_code == 201
    assert r.json()["email"] == "marcelo@tigre.org"


async def test_signup_email_invalido_422(client):
    r = client.post("/auth/signup", json={**_VALID_SIGNUP, "email": "not-an-email"})
    assert r.status_code == 422


async def test_signup_uf_lowercase_422(client):
    r = client.post("/auth/signup", json={**_VALID_SIGNUP, "oab_uf": "pe"})
    assert r.status_code == 422


async def test_signup_oab_invalida_422(client):
    r = client.post("/auth/signup", json={**_VALID_SIGNUP, "oab_numero": "abc"})
    assert r.status_code == 422


async def test_signup_senha_curta_422(client):
    r = client.post("/auth/signup", json={**_VALID_SIGNUP, "password": "short"})
    assert r.status_code == 422


async def test_login_sucesso_retorna_token(client):
    client.post("/auth/signup", json=_VALID_SIGNUP)
    r = client.post(
        "/auth/login",
        json={"email": _VALID_SIGNUP["email"], "password": _VALID_SIGNUP["password"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"].count(".") == 2  # JWT tem 3 segmentos


async def test_login_senha_errada_401(client):
    client.post("/auth/signup", json=_VALID_SIGNUP)
    r = client.post(
        "/auth/login",
        json={"email": _VALID_SIGNUP["email"], "password": "wrongwrongwrong"},
    )
    assert r.status_code == 401


async def test_login_email_inexistente_401(client):
    r = client.post(
        "/auth/login",
        json={"email": "naoexiste@nada.com", "password": "qualquer123"},
    )
    assert r.status_code == 401


async def test_me_sem_token_401(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


async def test_me_token_invalido_401(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


async def test_me_com_token_valido(client):
    sr = client.post("/auth/signup", json=_VALID_SIGNUP)
    user_id = sr.json()["id"]
    lr = client.post(
        "/auth/login",
        json={"email": _VALID_SIGNUP["email"], "password": _VALID_SIGNUP["password"]},
    )
    token = lr.json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["id"] == user_id
    assert r.json()["email"] == _VALID_SIGNUP["email"]


def test_jwt_sem_secret_levanta(monkeypatch):
    """Não deve haver fallback hardcoded — JWT_SECRET ausente é erro."""
    from nexus.auth.jwt import create_access_token

    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        create_access_token("subject")


def test_jwt_secret_curto_levanta(monkeypatch):
    """Secret < 32 chars é rejeitado — proteção contra brute-force."""
    from nexus.auth.jwt import create_access_token

    monkeypatch.setenv("JWT_SECRET", "short")
    with pytest.raises(RuntimeError, match="muito curto"):
        create_access_token("subject")


def test_jwt_token_expirado_levanta_jwterror(monkeypatch):
    """Token expirado deve falhar no decode."""
    monkeypatch.setenv(
        "JWT_SECRET", "test-secret-with-at-least-32-characters-please"
    )
    monkeypatch.setenv("JWT_TTL_MINUTES", "-1")  # já nasce expirado

    from nexus.auth.jwt import create_access_token, decode_access_token

    token = create_access_token("anyone")
    with pytest.raises(JWTError):
        decode_access_token(token)
