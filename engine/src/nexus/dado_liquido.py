from __future__ import annotations

import re

from .models import Fato, StatusFato

# Esquemas aceitos para fonte primária — qualquer outro derruba a auditoria
FONTE_PATTERN = re.compile(r"^(log_pje|certidao|hash|audio|video|peticao)://[^\s]+$")


def fonte_valida(fato: Fato) -> bool:
    return fato.fonte is not None and bool(FONTE_PATTERN.match(fato.fonte.uri))


def avaliar(fato: Fato) -> StatusFato:
    if not fonte_valida(fato):
        return StatusFato.PENDENTE
    if fato.verificado is None or not fato.verificado.strip():
        return StatusFato.PENDENTE
    return StatusFato.LIQUIDO
