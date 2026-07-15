"""Cérebro decisivo que aplica as diretrizes retóricas conforme o `modo_redacional`.

Temperatura Zero Invariante: o system prompt permanece imutável (cache hits);
apenas a diretriz retórica varia dentro da mensagem do usuário. O acoplamento com o
Módulo Hunter dá-se por `DraftRequest.dados_hunter` (payload do DossierHunter).
"""

from __future__ import annotations

import enum

from pydantic import BaseModel, Field

from schema.dossier_hunter import DossierHunterSchema


class ModoRedacional(str, enum.Enum):
    """Modos retóricos do endpoint /draft/llm."""

    PERTINAZ = "PERTINAZ"              # Nulidade + mérito equilibrados — combatividade padrão
    PREQUESTIONADOR = "PREQUESTIONADOR"  # Planta prequestionamento p/ REsp/RExt
    CUSTODIA = "CUSTODIA"             # Tese cautelar (liberdade imediata) no topo
    NULIDADE = "NULIDADE"            # Micro-desconstrução processual, vício a vício


class DraftRequest(BaseModel):
    """Requisição de redação, já acoplada ao payload do Hunter."""

    modo: ModoRedacional = Field(default=ModoRedacional.PERTINAZ)
    conteudo_base: str = Field(..., description="Texto base extraído do dossiê do caso")
    dados_hunter: DossierHunterSchema = Field(
        ..., description="Contrato validado produzido pelo Módulo Hunter"
    )


# Diretrizes retóricas indexadas por modo — definidas uma vez, imutáveis.
_INSTRUCOES: Dict[ModoRedacional, str] = {
    ModoRedacional.PERTINAZ: (
        "Escreva mantendo o equilíbrio rigoroso entre as nulidades preliminares e o "
        "mérito absolutório. Adote a combatividade padrão do padrão Tier 0."
    ),
    ModoRedacional.PREQUESTIONADOR: (
        "Foque explicitamente no prequestionamento para as instâncias superiores "
        "(STJ e STF). Invoque nominalmente cada dispositivo infraconstitucional e "
        "constitucional violado, estruturando a peça para viabilizar a subida de "
        "futuro REsp ou RExt."
    ),
    ModoRedacional.CUSTODIA: (
        "Priorize a tese cautelar de liberdade imediata. Insira o pedido de revogação "
        "da prisão preventiva ou aplicação de medidas alternativas (Art. 319 do CPP) "
        "no topo hierárquico dos requerimentos ordinários."
    ),
    ModoRedacional.NULIDADE: (
        "Adote uma estratégia de micro-desconstrução processual analítica. Disseque a "
        "peça vício a vício, expondo de forma isolada e sequencial cada quebra de "
        "cadeia de custódia e desvio de competência."
    ),
}


class DraftEngine:
    """Compõe a instrução retórica sem tocar no system prompt (cache-friendly)."""

    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = templates_dir

    def compor_instrucao_retorica(self, request: DraftRequest) -> str:
        """Devolve o bloco síncrono estruturado (diretriz + conteúdo base)."""
        diretriz = _INSTRUCOES.get(request.modo, _INSTRUCOES[ModoRedacional.PERTINAZ])
        return (
            f"[DIRETRIZ RETÓRICA - MODO {request.modo.value}]: {diretriz}\n\n"
            f"[CONTEÚDO BASE]: {request.conteudo_base}"
        )
