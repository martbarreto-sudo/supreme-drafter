from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class StatusFato(str, Enum):
    LIQUIDO = "LIQUIDO"
    PENDENTE = "PENDENTE"
    DESCARTADO = "DESCARTADO"


class FontePrimaria(BaseModel):
    uri: str = Field(..., description="ex.: log_pje://..., certidao://..., hash://...")
    descricao: str | None = None


class Fato(BaseModel):
    id: str
    proposto: str
    verificado: str | None = None
    fonte: FontePrimaria | None = None
    status: StatusFato = StatusFato.PENDENTE
    # dispositivo=False marca fato argumentativo/hipotético — não dispara HALT
    dispositivo: bool = True


class Vulnerabilidade(BaseModel):
    fato_id: str
    proposto: str
    realidade_verificada: str
    fonte: FontePrimaria | None = None
    status: StatusFato
    impacto: str


class Feito(BaseModel):
    id: str
    quadrante: str
    eixo_dogmatico: str
    tribunal_destino: str | None = Field(
        default=None,
        description="Destinatário processual da peça (ex.: 'STJ', 'TJ-PE — 2ª Vara Criminal'). "
        "Curador humano confirma antes do protocolo.",
    )
    fontes_silenciadas: list[str] = Field(
        default_factory=list,
        description="Auditoria de Silêncio — documentos/atos que DEVERIAM estar nos autos "
        "para sustentar a acusação e NÃO estão. Cada item entra como linha do bloco "
        "AUDITORIA DE SILÊNCIO da minuta e como prova negativa contra o Estado.",
    )
    vulnerabilidades: list[Vulnerabilidade] = Field(default_factory=list)


# Catálogo de peças cobertas (alinhado com M Advogado Criminalista —
# vide docs/audit-drive-gems.md §4). Adicionar peca_tipo aqui exige também
# criar template Jinja2 em templates/{peca_tipo.lower()}.md.j2 para a rota
# determinística /draft; o /draft/llm aceita qualquer tipo via prompt.
PecaTipo = Literal[
    "HC",                  # Habeas Corpus
    "RHC",                 # Recurso Ordinário em Habeas Corpus
    "AGRG",                # Agravo Regimental (em HC, REsp, RExt etc)
    "AGRAVO",              # alias retro-compat — preferir AGRG
    "RCL",                 # Reclamação Constitucional (STF/STJ)
    "APELACAO",            # Razões/Memoriais de Apelação criminal
    "MEMORIAIS",           # Memoriais Defensivos (alegações finais, júri)
    "RESPOSTA_ACUSACAO",   # Resposta à Acusação (art. 396-A CPP)
    "EDCL",                # Embargos de Declaração
    "MANIFESTACAO",        # Manifestação Defensiva (medidas protetivas etc)
]


class DraftRequest(BaseModel):
    feito_id: str
    peca_tipo: PecaTipo
    fatos: list[Fato]


class HaltResponse(BaseModel):
    halt: Literal[True] = True
    motivo: str
    vicios: list[str]
    acao_purgacao: str


class Minuta(BaseModel):
    halt: Literal[False] = False
    feito_id: str
    peca_tipo: PecaTipo
    texto: str
    fatos_usados: list[str]
    auditoria_silencio: list[str]
