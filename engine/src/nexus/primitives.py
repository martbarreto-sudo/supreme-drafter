"""Primitivos de proveniência — camada base, sem dependências internas.

Vivem aqui (e não em models.py) para que módulos como `dossier.schema`
possam reusá-los sem criar import circular com models. models.py os
re-exporta para manter `from nexus.models import FontePrimaria, StatusFato`.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class StatusFato(str, Enum):
    LIQUIDO = "LIQUIDO"
    PENDENTE = "PENDENTE"
    DESCARTADO = "DESCARTADO"


class FontePrimaria(BaseModel):
    uri: str = Field(..., description="ex.: log_pje://..., certidao://..., hash://...")
    descricao: str | None = None
