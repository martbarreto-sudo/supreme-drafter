from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AuditSummary(BaseModel):
    """Linha do histórico — sem texto, para listagem rápida."""

    id: str
    feito_id: str
    peca_tipo: str
    quality_score: int
    modelo: str
    created_at: datetime


class AuditDetail(AuditSummary):
    """Detalhe incluindo o texto da minuta carregado do disco."""

    minuta: str
    usage: dict[str, int]
