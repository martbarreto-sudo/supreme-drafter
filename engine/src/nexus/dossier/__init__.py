"""DossierHunter — contrato de entrada do DEEP HUNTER.

Encapsula os metadados de varredura do PJe focando em atritos de legalidade
ocultos (desvio de juiz natural, quebra de cadeia de custódia, omissões
mandatórias do Estado). Ver docs/audit-drive-gems.md §5.
"""

from .adapter import dossier_para_fontes_silenciadas
from .schema import (
    AtoProcessual,
    DadosBasicos,
    DesvioMagistrado,
    DossierHunterSchema,
    FiltrosOmissao,
    LacunaSequencial,
    MidiaPericia,
    Proveniencia,
)

__all__ = [
    "AtoProcessual",
    "DadosBasicos",
    "DesvioMagistrado",
    "DossierHunterSchema",
    "FiltrosOmissao",
    "LacunaSequencial",
    "MidiaPericia",
    "Proveniencia",
    "dossier_para_fontes_silenciadas",
]
