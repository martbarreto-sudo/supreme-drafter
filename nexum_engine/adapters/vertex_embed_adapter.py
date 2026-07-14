"""Adaptador de embeddings sobre um cliente Vertex injetado.

Injeção de dependência pura: o cliente concreto (SDK Google) entra no
gatilho HITL. O contrato exigido do cliente injetado é mínimo:

    async def embed(*, model: str, texts: Sequence[str]) -> Sequence[Sequence[float]]

O adaptador valida a resposta (um vetor por texto, não vazio) para que
falhas do provedor não contaminem silenciosamente a base RAG.
"""

from __future__ import annotations

from typing import Any, Sequence


class ClienteEmbedNaoInjetadoError(RuntimeError):
    """O cliente de embeddings do Vertex ainda não foi injetado (HITL)."""


class RespostaEmbedInvalidaError(RuntimeError):
    """O provedor devolveu embeddings em quantidade ou formato inválido."""


class VertexEmbedAdapter:
    """Implementa ``ports.EmbedderPort`` delegando a um cliente Vertex."""

    def __init__(self, client: Any | None = None, *, modelo: str = "") -> None:
        if client is not None and not modelo:
            raise ValueError("informe o nome do modelo de embedding do Vertex")
        self._client = client
        self._modelo = modelo

    async def embed(self, textos: Sequence[str]) -> list[list[float]]:
        if self._client is None:
            raise ClienteEmbedNaoInjetadoError(
                "cliente Vertex ausente: injete-o no gatilho HITL "
                "(VertexEmbedAdapter(client=..., modelo='...'))."
            )
        if not textos:
            return []
        vetores = await self._client.embed(model=self._modelo, texts=list(textos))
        resultado = [list(map(float, v)) for v in vetores]
        if len(resultado) != len(textos) or any(not v for v in resultado):
            raise RespostaEmbedInvalidaError(
                f"esperava {len(textos)} vetores não vazios, "
                f"recebi {len(resultado)}."
            )
        return resultado
