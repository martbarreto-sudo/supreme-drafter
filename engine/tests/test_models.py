"""Smoke tests do schema PecaTipo expandido.

PecaTipo virou o catálogo das peças do M Advogado Criminalista
(vide docs/audit-drive-gems.md §4). Esses testes garantem que a
validação Pydantic aceita os valores certos e barra o resto.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from nexus.models import DraftRequest


_BASE = {
    "feito_id": "Feito-HBM",
    "fatos": [
        {"id": "f1", "proposto": "X", "dispositivo": False}
    ],
}


@pytest.mark.parametrize(
    "tipo",
    [
        "HC", "RHC", "AGRG", "AGRAVO", "RCL", "APELACAO",
        "MEMORIAIS", "RESPOSTA_ACUSACAO", "EDCL", "MANIFESTACAO",
    ],
)
def test_peca_tipo_valido_aceita(tipo):
    req = DraftRequest(**_BASE, peca_tipo=tipo)
    assert req.peca_tipo == tipo


def test_peca_tipo_invalido_rejeita():
    with pytest.raises(ValidationError):
        DraftRequest(**_BASE, peca_tipo="PARECER")


def test_peca_tipo_case_sensitive():
    """Pydantic Literal é case-sensitive — 'hc' minúsculo é rejeitado."""
    with pytest.raises(ValidationError):
        DraftRequest(**_BASE, peca_tipo="hc")
