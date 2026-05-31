"""Fixtures compartilhadas para testes assíncronos.

Engine SQLite in-memory por teste (isolamento total). Schema criado via
Base.metadata.create_all em vez de Alembic — testes não exercitam migrations.
Migrations são testadas separadamente em test_migrations.py (Fase futura).

Fixture `client` provê um TestClient com JWT_SECRET configurado e a
sessão SQLite injetada via dependency_override de get_session. Usar nos
testes que batem na API HTTP.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from nexus.db import models  # noqa: F401 — registra tabelas
from nexus.db.base import Base


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sm = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with sm() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def client(monkeypatch, db_session):
    """TestClient com JWT_SECRET + override de get_session apontando para SQLite in-memory."""
    from fastapi.testclient import TestClient

    from nexus.api import app
    from nexus.db.session import get_session

    monkeypatch.setenv(
        "JWT_SECRET", "test-secret-with-at-least-32-characters-please"
    )
    monkeypatch.setenv("JWT_TTL_MINUTES", "15")

    async def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    yield TestClient(app)
    app.dependency_overrides.clear()


_DEFAULT_SIGNUP = {
    "email": "user@example.com",
    "name": "Default User",
    "oab_numero": "12345",
    "oab_uf": "PE",
    "password": "senhaForte12345",
    "aceito_tos": True,
    "tos_version": 1,  # mantenha em sync com legal.disclaimer.TOS_VERSION_ATUAL
}


def signup_and_login(client, **overrides) -> tuple[dict, str]:
    """Helper: faz signup + login e retorna (user_dict, jwt_token).

    Uso: `user, token = signup_and_login(client, email="other@x.com")`
    """
    payload = {**_DEFAULT_SIGNUP, **overrides}
    sr = client.post("/auth/signup", json=payload)
    assert sr.status_code == 201, sr.json()
    user = sr.json()
    lr = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert lr.status_code == 200, lr.json()
    return user, lr.json()["access_token"]
