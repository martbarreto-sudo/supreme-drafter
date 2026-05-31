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
    vulnerabilidades: list[Vulnerabilidade] = Field(default_factory=list)


PecaTipo = Literal["HC", "RHC", "AGRAVO", "MEMORIAIS"]


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
