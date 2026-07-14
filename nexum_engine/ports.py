"""Contratos (Protocols) da NEXUM Engine v5.5 — baixo acoplamento por desenho.

A engine depende só destes contratos; os adaptadores concretos
(``nexum_engine/adapters/``) os implementam por duck typing. Nenhum contrato
importa SDK de nuvem — as credenciais reais (Supabase/asyncpg, AnthropicVertex,
Anthropic direta) entram por injeção de dependência no gatilho HITL, nunca
em import de módulo.
"""

from __future__ import annotations

from typing import Any, Protocol, Sequence, runtime_checkable


@runtime_checkable
class DatabasePort(Protocol):
    """Acesso ao PostgreSQL (Supabase, isolado por Row-Level Security)."""

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        """Executa a consulta e devolve todas as linhas como dicts."""
        ...

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        """Executa a consulta e devolve a primeira linha (ou None)."""
        ...

    async def execute(self, query: str, *args: Any) -> str:
        """Executa um comando (INSERT/UPDATE/...) e devolve o status."""
        ...


@runtime_checkable
class EmbedderPort(Protocol):
    """Geração de embeddings para busca semântica (RAG)."""

    async def embed(self, textos: Sequence[str]) -> list[list[float]]:
        """Devolve um vetor por texto, na mesma ordem da entrada."""
        ...


@runtime_checkable
class CompletionPort(Protocol):
    """Geração de texto por um modelo Claude (agente paralelo ou consolidador)."""

    async def gerar(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 16000,
    ) -> str:
        """Envia o prompt e devolve o texto da resposta."""
        ...
