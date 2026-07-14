"""NEXUM Engine v5.5 — fundação de contratos e adaptadores.

Arquitetura hexagonal mínima: ``ports.py`` define os contratos (Protocols),
``adapters/`` traz as implementações concretas com injeção de dependência
pura (credenciais só entram no gatilho HITL), e ``models.py`` é o cânone
único de model IDs com bloqueio de regressão.
"""

from .models import (
    MODELO_AGENTE_PARALELO,
    MODELO_CONSOLIDADOR,
    ModeloInvalidoError,
    validar_modelo,
)
from .ports import CompletionPort, DatabasePort, EmbedderPort

__all__ = [
    "MODELO_AGENTE_PARALELO",
    "MODELO_CONSOLIDADOR",
    "ModeloInvalidoError",
    "validar_modelo",
    "CompletionPort",
    "DatabasePort",
    "EmbedderPort",
]
