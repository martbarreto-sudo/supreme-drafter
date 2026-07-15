"""Contrato Pydantic v2 do DossierHunter (DEEP HUNTER).

Princípio-raiz — AFIRMAÇÃO ≠ OMISSÃO:
- AFIRMAÇÃO (algo existe nos autos) exige `fonte: FontePrimaria`; nasce
  PENDENTE e só vira dado dispositivo após o Módulo 11 / HALT.
- OMISSÃO (algo que deveria existir e não existe) é o próprio achado —
  prova negativa contra o Estado. Não carrega fonte positiva; alimenta a
  Auditoria de Silêncio (`fontes_silenciadas` do Feito) via adapter.

O output do hunter é NÃO-CONFIÁVEL até liquidação: reusa StatusFato e
FontePrimaria do núcleo para não duplicar vocabulário de proveniência.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from ..primitives import FontePrimaria, StatusFato

# Máscara CNJ NNNNNNN-DD.AAAA.J.TR.OOOO. v1 valida só o formato — o dígito
# verificador (módulo 97) fica para depois, para não rejeitar NPU real legado
# por bug de cálculo.
_NPU_RE = re.compile(r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$")


class DadosBasicos(BaseModel):
    npu: str
    tribunal: str
    orgao_julgador: str
    classe: str
    assunto: str | None = None
    # Se True, o pipeline emite aviso de manejo LGPD (v1 não barra persistência).
    segredo_justica: bool = False

    @field_validator("npu")
    @classmethod
    def _valida_npu(cls, v: str) -> str:
        if not _NPU_RE.match(v):
            raise ValueError(
                "NPU fora do padrão CNJ NNNNNNN-DD.AAAA.J.TR.OOOO"
            )
        return v


class AtoProcessual(BaseModel):
    """Item da linha do tempo — AFIRMAÇÃO (exige fonte)."""

    id_evento: str
    sequencial: int | None = None
    data: date
    tipo_documento: str
    id_documento: str | None = None
    fonte: FontePrimaria


class DesvioMagistrado(BaseModel):
    """Desvio de juiz natural: ato prolatado por não-titular.

    Se `portaria_designacao` está presente → designação regular (AFIRMAÇÃO).
    Se ausente → OMISSÃO candidata a fontes_silenciadas. O booleano-espelho
    `portaria_publica_localizada` é forçado a refletir o Optional (filtro O(1)).
    """

    juiz_prolator: str
    juiz_titular: str | None = None
    data_ato: date
    ato_referencia: str  # id_evento do ato sob suspeita (aponta p/ linha_tempo_atos)
    portaria_designacao: FontePrimaria | None = None
    portaria_publica_localizada: bool = False
    status: StatusFato = StatusFato.PENDENTE

    @model_validator(mode="after")
    def _coerencia_portaria(self) -> DesvioMagistrado:
        # Espelho booleano nunca diverge do Optional: presença ⇒ True, ausência ⇒ False.
        self.portaria_publica_localizada = self.portaria_designacao is not None
        return self

    @property
    def eh_omissao(self) -> bool:
        return self.portaria_designacao is None


class MidiaPericia(BaseModel):
    """Cadeia de custódia técnica — mídia sem hash é mídia sem integridade
    comprovada (art. 158-A ss. CPP)."""

    id_documento: str
    tipo_midia: str  # AUDIO, VIDEO, EXTRACAO_CELEBRITE, ...
    hash_presente: bool
    hash_algoritmo: str | None = None
    hash_valor: str | None = None
    metadados_extraidos: dict[str, str] = Field(default_factory=dict)
    cadeia_custodia_integra: bool = False

    @model_validator(mode="after")
    def _exige_hash(self) -> MidiaPericia:
        if self.hash_presente and (not self.hash_algoritmo or not self.hash_valor):
            raise ValueError(
                "hash_presente=True exige hash_algoritmo e hash_valor não-nulos"
            )
        return self


class LacunaSequencial(BaseModel):
    """Gap de IDs sequenciais no PJe — dado estrutural, não prosa."""

    de: int
    ate: int
    contexto: str = ""

    @model_validator(mode="after")
    def _ordem(self) -> LacunaSequencial:
        if self.ate < self.de:
            raise ValueError("lacuna inválida: 'ate' não pode ser menor que 'de'")
        return self


class FiltrosOmissao(BaseModel):
    """Ausências mandatórias do Estado — o alvo do módulo."""

    omissao_analise_contemporaneidade: bool = False
    ausencia_ata_plenario: bool = False
    quebra_sequencial_ids: list[LacunaSequencial] = Field(default_factory=list)
    omissoes_livres: list[str] = Field(default_factory=list)


class Proveniencia(BaseModel):
    """Meta do próprio scan — de onde veio e quão confiável é."""

    metodo: Literal["AUTO_EXTRACAO", "CONFIRMADO_HUMANO"] = "AUTO_EXTRACAO"
    capturado_em: datetime
    hunter_versao: str | None = None


class DossierHunterSchema(BaseModel):
    dados_basicos: DadosBasicos
    linha_tempo_atos: list[AtoProcessual] = Field(default_factory=list)
    auditoria_magistrados: list[DesvioMagistrado] = Field(default_factory=list)
    midias_e_pericias: list[MidiaPericia] = Field(default_factory=list)
    filtros_omissao: FiltrosOmissao = Field(default_factory=FiltrosOmissao)
    proveniencia: Proveniencia
