"""Adaptador PostgreSQL (Supabase) sobre um ``asyncpg.Pool`` injetado.

Injeção de dependência pura: este módulo não importa ``asyncpg`` nem lê
credenciais. O pool real é criado pelo operador no gatilho HITL
(``asyncpg.create_pool(dsn=...)``) e passado ao construtor. Sem o pool,
qualquer consulta falha com uma mensagem que aponta o passo pendente.
"""

from __future__ import annotations

from typing import Any


class PoolNaoInjetadoError(RuntimeError):
    """O asyncpg.Pool do Supabase ainda não foi injetado (gatilho HITL)."""


class AsyncpgAdapter:
    """Implementa ``ports.DatabasePort`` delegando a um asyncpg.Pool."""

    def __init__(self, pool: Any | None = None) -> None:
        self._pool = pool

    def _exigir_pool(self) -> Any:
        if self._pool is None:
            raise PoolNaoInjetadoError(
                "asyncpg.Pool ausente: injete o pool do Supabase no gatilho "
                "HITL (AsyncpgAdapter(pool=await asyncpg.create_pool(dsn)))."
            )
        return self._pool

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        registros = await self._exigir_pool().fetch(query, *args)
        return [dict(r) for r in registros]

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        registro = await self._exigir_pool().fetchrow(query, *args)
        return dict(registro) if registro is not None else None

    async def execute(self, query: str, *args: Any) -> str:
        return await self._exigir_pool().execute(query, *args)
