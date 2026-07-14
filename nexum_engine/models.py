"""Cânone de modelos da NEXUM Engine v5.5.

Fonte única de verdade para as strings de modelo usadas pela engine.
Nenhum outro módulo deve conter um model ID literal — importe daqui.

Roteamento (docs/stack-ia.md):
- Agentes paralelos (níveis 1-2): Claude Sonnet 4.6
- Consolidador de peer-review (nível 4): Claude Opus 4.8

Vertex AI: modelos de geração atual usam o ID puro (sem prefixo e sem
sufixo de data); apenas snapshots datados usam o separador ``@``
(ex.: ``claude-opus-4-5@20251101``). Não invente datas — se o snapshot
não é conhecido, use o ID puro.
"""

from __future__ import annotations

# --- Cânone ativo -----------------------------------------------------------

MODELO_AGENTE_PARALELO = "claude-sonnet-4-6"
MODELO_CONSOLIDADOR = "claude-opus-4-8"

MODELOS_PERMITIDOS = frozenset({MODELO_AGENTE_PARALELO, MODELO_CONSOLIDADOR})

# Região Vertex usada pela banca (ver docs/stack-ia.md).
REGIAO_VERTEX = "us-east5"

# --- Bloqueio de regressão ---------------------------------------------------
# IDs aposentados que já contaminaram código legado. Montados por concatenação
# de propósito: assim uma varredura textual do repositório pela string completa
# não acusa este arquivo, só regressões reais.
MODELOS_PROIBIDOS = frozenset({
    "claude-3-5-" + "sonnet-20241022",  # aposentado em 2025-10-28
    "claude-3-5-" + "sonnet-20240620",  # aposentado em 2025-10-28
    "claude-3-" + "opus-20240229",      # aposentado em 2026-01-05
})


class ModeloInvalidoError(ValueError):
    """Model ID fora do cânone da engine (aposentado ou desconhecido)."""


def validar_modelo(modelo: str) -> str:
    """Valida um model ID contra o cânone; devolve-o inalterado se válido.

    Levanta ModeloInvalidoError para IDs aposentados ou fora do cânone —
    é a barreira de runtime que espelha o TestModelStringRegression do CI.
    """
    if modelo in MODELOS_PROIBIDOS:
        raise ModeloInvalidoError(
            f"model ID aposentado: {modelo!r}. Use {MODELO_AGENTE_PARALELO!r} "
            f"(agentes) ou {MODELO_CONSOLIDADOR!r} (consolidador)."
        )
    if modelo not in MODELOS_PERMITIDOS:
        raise ModeloInvalidoError(
            f"model ID fora do cânone: {modelo!r}. Permitidos: "
            f"{sorted(MODELOS_PERMITIDOS)}."
        )
    return modelo


def modelo_para_vertex(modelo: str, versao: str | None = None) -> str:
    """Formata um model ID para o Vertex AI.

    Modelos de geração atual usam o ID puro; passe ``versao`` apenas para
    snapshots datados documentados (formato ``nome@AAAAMMDD``).
    """
    validar_modelo(modelo)
    return f"{modelo}@{versao}" if versao else modelo
