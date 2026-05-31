"""Async SQLAlchemy engine + session.

Engine e sessionmaker são lazy — só criados na primeira chamada. Isso permite que
testes injetem `DATABASE_URL` via monkeypatch antes do primeiro uso, e que o app
boote sem DB configurado (apenas falhe quando alguém realmente pede sessão).
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL não configurado")
    return url


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(_database_url(), pool_pre_ping=True)
    return _engine


def _get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)
    return _sessionmaker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: produz uma AsyncSession por request."""
    sm = _get_sessionmaker()
    async with sm() as session:
        yield session


def reset_engine_for_tests() -> None:
    """Limpa singletons — testes que mudam DATABASE_URL devem chamar isto."""
    global _engine, _sessionmaker
    _engine = None
    _sessionmaker = None
