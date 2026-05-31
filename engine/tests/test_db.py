"""Smoke tests do modelo User — schema cria, insere, busca, unique em email."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from nexus.db.models import OABStatus, User


async def test_pode_inserir_e_buscar_user(db_session):
    user = User(
        email="marcelo@example.com",
        name="Marcelo Tigre",
        oab_numero="27543",
        oab_uf="PE",
        password_hash="$2b$12$placeholder",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id  # UUID gerado pelo default da coluna
    assert user.oab_status == OABStatus.PENDING_DECLARATION
    assert user.created_at is not None
    assert user.tos_aceito_em is None


async def test_email_unique_constraint(db_session):
    db_session.add(
        User(
            email="dup@example.com",
            name="A",
            oab_numero="111",
            oab_uf="PE",
            password_hash="x",
        )
    )
    await db_session.commit()

    db_session.add(
        User(
            email="dup@example.com",
            name="B",
            oab_numero="222",
            oab_uf="SP",
            password_hash="y",
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_busca_por_email(db_session):
    db_session.add(
        User(
            email="busca@example.com",
            name="Teste",
            oab_numero="999",
            oab_uf="DF",
            password_hash="x",
        )
    )
    await db_session.commit()

    result = await db_session.execute(
        select(User).where(User.email == "busca@example.com")
    )
    found = result.scalar_one()
    assert found.name == "Teste"
    assert found.oab_uf == "DF"
