"""Loop de verdade da NEXUM Engine — precedentes verificados e auditoria."""

from .auditor import RelatorioAuditoria, auditar_citacoes, extrair_citacoes
from .fontes import FonteDePrecedentes, FonteJsonVerificada, FonteSupabase
from .precedente import Precedente, normalizar_citacao

__all__ = [
    "FonteDePrecedentes",
    "FonteJsonVerificada",
    "FonteSupabase",
    "Precedente",
    "RelatorioAuditoria",
    "auditar_citacoes",
    "extrair_citacoes",
    "normalizar_citacao",
]
