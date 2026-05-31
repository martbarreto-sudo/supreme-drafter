"""Fixtures compartilhadas para testes assíncronos.

Engine SQLite in-memory por teste (isolamento total). Schema criado via
Base.metadata.create_all em vez de Alembic — testes não exercitam migrations.
Migrations são testadas separadamente em test_migrations.py (Fase futura).
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
