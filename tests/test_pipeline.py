"""Testes do pipeline com cliente falso (sem rede)."""

from __future__ import annotations

import pytest

from deep_hunter import Modo, Peca, Pipeline
from tests.conftest import FakeClient

DOSSIE = {
    "resumo_executivo": "Prova digital sem hash.",
    "modo": "SIMBIOSE",
    "cronologia": [{"data": "2025-01-01", "evento": "Apreensão", "fls": "fls. 12"}],
    "dossie_vulnerabilidades": [
        {
            "id": "VULN-01",
            "categoria": "MESMIDADE_HASH",
            "descricao": "Extração manual sem hash.",
            "fls": "fls. 40",
            "gravidade": "NUCLEO_FIDEDIGNIDADE",
            "impacto": "Nulidade absoluta.",
        }
    ],
    "tabela_nulidades": [
        {
            "vulnerabilidade_id": "VULN-01",
            "tese": "Violação da mesmidade.",
            "dispositivo": "Art. 158-B CPP; ISO 27037",
            "sniper_precedent": "AgRg no HC 828.054-RN",
            "fls_ancora": "fls. 40",
        }
    ],
    "lacunas_de_grounding": [],
}


@pytest.fixture
def pdf(tmp_path):
    p = tmp_path / "autos.pdf"
    p.write_bytes(b"%PDF-1.4\n%%EOF\n")
    return p


def test_audit_devolve_dossie(pdf):
    client = FakeClient(dossie=DOSSIE)
    pipeline = Pipeline(client=client)
    dossie = pipeline.audit(pdf, modo=Modo.FORENSE)
    assert dossie["dossie_vulnerabilidades"][0]["id"] == "VULN-01"
    # Deep Hunter usa structured outputs (format presente) e sem citações no PDF.
    call = client.calls[0]
    assert "format" in call["output_config"]
    pdf_block = call["messages"][0]["content"][0]
    assert "citations" not in pdf_block


def test_draft_usa_apenas_dossie(pdf):
    client = FakeClient(dossie=DOSSIE, peca="# HC\n\nfls. 40 — nulidade.")
    pipeline = Pipeline(client=client)
    peca = pipeline.draft(DOSSIE, peca=Peca.HABEAS_CORPUS)
    assert "fls. 40" in peca
    # O dossiê inteiro é injetado na instrução do redator.
    instrucao = client.calls[-1]["messages"][0]["content"]
    assert "AgRg no HC 828.054-RN" in instrucao


def test_run_ponta_a_ponta(pdf):
    client = FakeClient(dossie=DOSSIE)
    pipeline = Pipeline(client=client)
    resultado = pipeline.run(pdf, modo="SIMBIOSE", peca="memorial")
    assert resultado.dossie == DOSSIE
    assert resultado.peca_markdown
    assert len(client.calls) == 2  # auditoria + redação
