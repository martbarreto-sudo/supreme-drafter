"""Construção do cliente conforme o provedor — primeira parte ou Vertex AI.

O `Pipeline` sempre aceitou um cliente injectado (é o que a suíte usa), mas o
cliente construído por omissão era, até aqui, obrigatoriamente o de primeira
parte. Isto torna a comutação explícita e governada por ambiente, de modo que
operar dentro do perímetro de nuvem do cliente seja configuração, não refactor.

    DEEP_HUNTER_PROVEDOR=anthropic   # padrão: API comercial da Anthropic
    DEEP_HUNTER_PROVEDOR=vertex      # Claude servido no Google Cloud do cliente

Na rota Vertex, projecto e região saem de `ANTHROPIC_VERTEX_PROJECT_ID` e
`CLOUD_ML_REGION` (lidos pelo próprio SDK, que também resolve as credenciais por
ADC); passá-los explicitamente aqui apenas quando estão definidos preserva esse
encadeamento. Tudo o que o Deep Hunter exige do canal — PDF como bloco
`document`, saída estruturada, *adaptive thinking* com `effort` e streaming — é
suportado nas duas rotas, pelo que o resto do pipeline não muda uma linha.
"""

from __future__ import annotations

import os
from typing import Any

import anthropic

from .config import Provedor, RunConfig


def build_client(config: RunConfig | None = None) -> Any:
    """Devolve o cliente do provedor configurado.

    Levanta `ValueError` se o provedor for desconhecido (via `RunConfig`) e
    `ImportError`, com indicação do extra a instalar, se a rota Vertex for pedida
    sem as dependências do Google Cloud.
    """
    config = config or RunConfig()

    if config.provedor == Provedor.VERTEX.value:
        try:
            from anthropic import AnthropicVertex
        except ImportError as exc:  # pragma: no cover - depende do ambiente
            raise ImportError(
                "A rota Vertex exige as dependências do Google Cloud: "
                'instale `pip install "anthropic[vertex]"`.'
            ) from exc

        kwargs: dict[str, str] = {}
        if projecto := os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID"):
            kwargs["project_id"] = projecto
        if regiao := os.environ.get("CLOUD_ML_REGION"):
            kwargs["region"] = regiao
        return AnthropicVertex(**kwargs)

    return anthropic.Anthropic()
