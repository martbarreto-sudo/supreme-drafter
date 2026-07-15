"""Deep Hunter × Supreme Drafter — ecossistema de auditoria forense de prova digital.

Contrato unificado: `DossierHunterSchema` (Pydantic) + `ModoRedacional`.
"""

from __future__ import annotations

from core.draft_engine import DraftEngine, DraftRequest, ModoRedacional
from schema.dossier_hunter import DossierHunterSchema

from .agents import DeepHunter, SupremeDrafter
from .config import Comando, Modo, RunConfig
from .pipeline import Pipeline, Resultado

__all__ = [
    "Pipeline",
    "Resultado",
    "DeepHunter",
    "SupremeDrafter",
    "Modo",
    "Comando",
    "RunConfig",
    "DossierHunterSchema",
    "ModoRedacional",
    "DraftEngine",
    "DraftRequest",
]

__version__ = "0.2.0"
