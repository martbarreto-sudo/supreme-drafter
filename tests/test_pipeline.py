"""Testes do pipeline com cliente falso (sem rede) — contrato unificado."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from deep_hunter import Modo, ModoRedacional, Pipeline
from schema.dossier_hunter import DossierHunterSchema
from tests.conftest import FakeClient

# Dossiê válido no contrato unificado (datas em ISO 8601).
DOSSIE = {
    "npu": "0001258-15.2026.8.17.4002",
    "tribunal": "TJPE",
    "orgao_julgador": "Vara Criminal",
    "linha_tempo_atos": [
        {
            "id_documento": "12",
            "data_ato": "2026-01-10T09:00:00",
            "tipo_documento": "Decisão",
            "usuario_protocolo": "cert:JUIZ_X",
        }
    ],
    "auditoria_magistrados": [],
    "auditoria_custodia": [
        {
            "id_documento": "40",
            "tipo_midia": "CELLEBRITE_DUMP",
            "hash_declarado_estado": None,
            "possui_quebra_custodia": True,
        }
    ],
    "omissao_analise_contemporaneidade": True,
    "ausencia_ata_plenario": False,
    "quebra_sequencial_ids": False,
}


@pytest.fixture
def pdf(tmp_path):
    p = tmp_path / "autos.pdf"
    p.write_bytes(b"%PDF-1.4\n%%EOF\n")
    return p


def test_audit_devolve_contrato(pdf):
    client = FakeClient(dossie=DOSSIE)
    pipeline = Pipeline(client=client)
    dossie = pipeline.audit(pdf, modo=Modo.FORENSE)
    assert isinstance(dossie, DossierHunterSchema)
    assert dossie.npu == "0001258-15.2026.8.17.4002"
    assert dossie.auditoria_custodia[0].possui_quebra_custodia is True
    # Structured outputs nativo: o contrato vai como `output_format`, sem schema
    # montado à mão, e o PDF vai sem citações (incompatíveis com saída estruturada).
    call = client.calls[0]
    assert call["output_format"] is DossierHunterSchema
    assert "format" not in call["output_config"]
    pdf_block = call["messages"][0]["content"][0]
    assert "citations" not in pdf_block


def test_draft_usa_diretriz_e_resumo(pdf):
    client = FakeClient(dossie=DOSSIE, peca="# HC\n\nrevogação da preventiva.")
    pipeline = Pipeline(client=client)
    dossie = DossierHunterSchema.model_validate(DOSSIE)
    peca = pipeline.draft(dossie, modo=ModoRedacional.CUSTODIA)
    assert "revogação" in peca
    # A instrução carrega a diretriz do modo e o NPU (resumo derivado do dossiê).
    instrucao = client.calls[-1]["messages"][0]["content"]
    assert "[DIRETRIZ RETÓRICA - MODO CUSTODIA]" in instrucao
    assert "0001258-15.2026.8.17.4002" in instrucao


def test_run_ponta_a_ponta(pdf):
    client = FakeClient(dossie=DOSSIE)
    pipeline = Pipeline(client=client)
    resultado = pipeline.run(pdf, modo="SIMBIOSE", modo_redacional="NULIDADE")
    assert isinstance(resultado.dossie, DossierHunterSchema)
    assert resultado.peca_markdown
    assert len(client.calls) == 2  # auditoria + redação


def test_audit_devolve_modelo_validado_e_nao_texto(pdf):
    """O que sai do auditor é o contrato em si, não JSON por validar."""
    pipeline = Pipeline(client=FakeClient(dossie=DOSSIE))
    dossie = pipeline.audit(pdf)
    assert isinstance(dossie, DossierHunterSchema)
    assert dossie.linha_tempo_atos[0].data_ato.year == 2026  # datetime, não string


def test_audit_rejeita_dossie_fora_do_contrato(pdf):
    """Severidade preservada na migração: o SDK valida com TypeAdapter.validate_json.

    Um NPU fora do padrão CNJ tem de levantar — antes era o nosso
    `model_validate_json`, agora é o parse do próprio SDK.
    """
    ruim = {**DOSSIE, "npu": "NPU-INVENTADO"}
    pipeline = Pipeline(client=FakeClient(dossie=ruim))
    with pytest.raises(ValidationError):
        pipeline.audit(pdf)
