"""Deep Hunter × Supreme Drafter — ecossistema de auditoria forense de prova digital."""

from __future__ import annotations

from .agents import DeepHunter, SupremeDrafter
from .config import Comando, Modo, Peca, RunConfig
from .pipeline import Pipeline, Resultado

__all__ = [
    "Pipeline",
    "Resultado",
    "DeepHunter",
    "SupremeDrafter",
    "Modo",
    "Comando",
    "Peca",
    "RunConfig",
]

__version__ = "0.1.0"
