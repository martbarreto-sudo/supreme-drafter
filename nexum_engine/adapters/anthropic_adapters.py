"""Adaptadores Claude — Vertex AI e API direta — sobre clientes injetados.

Injeção de dependência pura: nenhum SDK é importado aqui e nenhuma
credencial é lida. No gatilho HITL o operador injeta:

- ``AnthropicVertexAdapter``: um ``anthropic.AsyncAnthropicVertex(project_id=..., region=...)``
  (autenticação via ADC do GCP; região da banca em ``models.REGIAO_VERTEX``).
- ``DirectAPIAdapter``: um ``anthropic.AsyncAnthropic()`` (ANTHROPIC_API_KEY).

Ambos os clientes expõem a mesma superfície ``messages.create``; os dois
adaptadores diferem apenas no modelo padrão do cânone e em como o model ID
é formatado (Vertex aceita o ID puro para modelos de geração atual).
"""

from __future__ import annotations

from typing import Any

from ..models import (
    MODELO_AGENTE_PARALELO,
    MODELO_CONSOLIDADOR,
    modelo_para_vertex,
    validar_modelo,
)


class ClienteLLMNaoInjetadoError(RuntimeError):
    """O cliente Anthropic ainda não foi injetado (gatilho HITL)."""


class RespostaSemTextoError(RuntimeError):
    """A resposta do modelo não contém nenhum bloco de texto."""


class _BaseClaudeAdapter:
    """Implementa ``ports.CompletionPort`` sobre um cliente injetado."""

    _modelo_padrao: str = ""

    def __init__(self, client: Any | None = None, *, modelo: str | None = None) -> None:
        self._client = client
        self._modelo = validar_modelo(modelo or self._modelo_padrao)

    @property
    def modelo(self) -> str:
        return self._modelo

    def _modelo_para_requisicao(self) -> str:
        return self._modelo

    async def gerar(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 16000,
    ) -> str:
        if self._client is None:
            raise ClienteLLMNaoInjetadoError(
                f"cliente ausente em {type(self).__name__}: injete-o no "
                "gatilho HITL antes de gerar."
            )
        kwargs: dict[str, Any] = {
            "model": self._modelo_para_requisicao(),
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system is not None:
            kwargs["system"] = system
        resposta = await self._client.messages.create(**kwargs)
        textos = [b.text for b in resposta.content if getattr(b, "type", "") == "text"]
        if not textos:
            raise RespostaSemTextoError(
                f"resposta sem bloco de texto (stop_reason="
                f"{getattr(resposta, 'stop_reason', None)!r})."
            )
        return "\n".join(textos)


class AnthropicVertexAdapter(_BaseClaudeAdapter):
    """Consolidador de peer-review (nível 4) via Vertex AI."""

    _modelo_padrao = MODELO_CONSOLIDADOR

    def __init__(
        self,
        client: Any | None = None,
        *,
        modelo: str | None = None,
        versao_snapshot: str | None = None,
    ) -> None:
        super().__init__(client, modelo=modelo)
        self._versao_snapshot = versao_snapshot

    def _modelo_para_requisicao(self) -> str:
        return modelo_para_vertex(self._modelo, self._versao_snapshot)


class DirectAPIAdapter(_BaseClaudeAdapter):
    """Agentes paralelos (níveis 1-2) via API direta da Anthropic."""

    _modelo_padrao = MODELO_AGENTE_PARALELO
