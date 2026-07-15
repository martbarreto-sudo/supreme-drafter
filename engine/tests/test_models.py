"""Smoke tests do schema PecaTipo expandido.

PecaTipo virou o catálogo das peças do M Advogado Criminalista
(vide docs/audit-drive-gems.md §4). Esses testes garantem que a
validação Pydantic aceita os valores certos e barra o resto.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from nexus.models import DraftRequest, ModoRedacional


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


# ---------- modo_redacional ----------


def test_modo_redacional_default_pertinaz():
    """Omitir o modo cai em PERTINAZ — retro-compatível com payloads antigos."""
    req = DraftRequest(**_BASE, peca_tipo="HC")
    assert req.modo_redacional == ModoRedacional.PERTINAZ


@pytest.mark.parametrize(
    "modo", ["PERTINAZ", "PREQUESTIONADOR", "CUSTODIA", "NULIDADE"]
)
def test_modo_redacional_valido_aceita(modo):
    req = DraftRequest(**_BASE, peca_tipo="HC", modo_redacional=modo)
    assert req.modo_redacional.value == modo


def test_modo_redacional_invalido_rejeita():
    with pytest.raises(ValidationError):
        DraftRequest(**_BASE, peca_tipo="HC", modo_redacional="TURBO")
