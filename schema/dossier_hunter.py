"""Contrato estrito (Pydantic v2) que governa os metadados extraídos pelo
caçador de atritos de legalidade (Módulo Hunter).

Correções de tipagem face à minuta v1:
  - `Field(regex=...)` → `Field(pattern=...)`  (v2 removeu `regex`)
  - `@validator`       → `@field_validator` + `@classmethod`  (v2)
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

# Padrão CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO
NPU_PATTERN = r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$"


class AttoCronologico(BaseModel):
    """Um ato processual na linha do tempo dos autos (PJe)."""

    id_documento: str = Field(..., description="ID numérico único do documento no PJe")
    data_ato: datetime = Field(..., description="Data e hora do protocolo do ato processual")
    tipo_documento: str = Field(..., description="Classificação formal do ato (Decisão, Certidão, Petição)")
    usuario_protocolo: str = Field(..., description="Credencial/certificado que assinou o ato")


class AuditoriaJuizNatural(BaseModel):
    """Auditoria de competência e do princípio do juiz natural."""

    juiz_prolator: str = Field(..., description="Magistrado que assinou a decisão")
    data_ato: datetime = Field(..., description="Data exata da assinatura do ato")
    portaria_designacao_hash: Optional[str] = Field(
        None, description="SHA-256 da portaria pública de designação extraordinária"
    )
    possui_desvio: bool = Field(False, description="Sinalizador de quebra de competência do juiz natural")


class MidiaPericiaCustodia(BaseModel):
    """Auditoria da cadeia de custódia de mídias e evidências materiais."""

    id_documento: str = Field(..., description="ID do anexo com a evidência material")
    tipo_midia: str = Field(..., description="Tipo do arquivo (MP4, WAV, CELLEBRITE_DUMP)")
    hash_declarado_estado: Optional[str] = Field(
        None, description="Hash (MD5/SHA-256) inserido pela acusação"
    )
    possui_quebra_custodia: bool = Field(
        True, description="Ausência de hash ou quebra sequencial de custódia"
    )


class DossierHunterSchema(BaseModel):
    """Payload agnóstico produzido pelo Módulo Hunter e consumido pelo Drafter."""

    npu: str = Field(..., pattern=NPU_PATTERN, description="Numeração Única de Processo (padrão CNJ)")
    tribunal: str = Field(..., description="Sigla do Tribunal de origem (TJPE, TRF6, STJ)")
    orgao_julgador: str = Field(..., description="Vara ou Câmara originária do processo")

    linha_tempo_atos: List[AttoCronologico] = Field(default_factory=list)
    auditoria_magistrados: List[AuditoriaJuizNatural] = Field(default_factory=list)
    auditoria_custodia: List[MidiaPericiaCustodia] = Field(default_factory=list)

    # Filtros de omissão mandatórios (omissões imputáveis ao Estado)
    omissao_analise_contemporaneidade: bool = Field(
        True, description="Ausência de fundamentação de fatos contemporâneos na preventiva"
    )
    ausencia_ata_plenario: bool = Field(False, description="Falta de juntada da ata de plenário do júri")
    quebra_sequencial_ids: bool = Field(False, description="Lacunas ou saltos nos IDs de documentos do PJe")

    @field_validator("npu")
    @classmethod
    def validar_formato_cnj(cls, v: str) -> str:
        if not v:
            raise ValueError("O campo NPU não pode ser vazio e deve seguir o formato do CNJ")
        return v
