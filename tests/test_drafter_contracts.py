"""Suíte de regressão sob premissa Zero-Credencial (100% isolada de rede)."""

from __future__ import annotations

import pytest

from core.draft_engine import DraftEngine, DraftRequest, ModoRedacional
from schema.dossier_hunter import DossierHunterSchema


def test_deve_aplicar_modo_default_pertinaz_quando_nao_especificado():
    payload_hunter = {
        "npu": "0001258-15.2026.8.17.4002",
        "tribunal": "TJPE",
        "orgao_julgador": "Vara Criminal",
    }

    # Valida conformidade do schema de entrada agnóstico
    hunter = DossierHunterSchema(**payload_hunter)
    assert hunter.omissao_analise_contemporaneidade is True

    request = DraftRequest(
        conteudo_base="Fato líquido do caso Éricles", dados_hunter=hunter.model_dump()
    )
    assert request.modo == ModoRedacional.PERTINAZ

    engine = DraftEngine()
    instrucao = engine.compor_instrucao_retorica(request)
    assert "[DIRETRIZ RETÓRICA - MODO PERTINAZ]" in instrucao


def test_deve_alterar_diretriz_retorica_para_modo_prequestionador():
    payload_hunter = {
        "npu": "0002318-23.2026.8.17.4002",
        "tribunal": "STJ",
        "orgao_julgador": "5a Turma",
    }

    request = DraftRequest(
        modo=ModoRedacional.PREQUESTIONADOR,
        conteudo_base="Fundamentação com base na Súmula 231",
        dados_hunter=payload_hunter,
    )

    engine = DraftEngine()
    instrucao = engine.compor_instrucao_retorica(request)
    assert "[DIRETRIZ RETÓRICA - MODO PREQUESTIONADOR]" in instrucao
    assert "Foque explicitamente no prequestionamento" in instrucao


def test_deve_rejeitar_npu_fora_do_padrao_cnj():
    with pytest.raises(ValueError):
        DossierHunterSchema(npu="NPU-INVALIDO-123", tribunal="TJPE", orgao_julgador="1a Vara")


def test_todos_os_modos_geram_diretriz_distinta():
    """Blindagem extra: cada modo produz um cabeçalho próprio."""
    engine = DraftEngine()
    payload = {"npu": "0001258-15.2026.8.17.4002", "tribunal": "TJPE", "orgao_julgador": "Vara"}
    cabecalhos = set()
    for modo in ModoRedacional:
        req = DraftRequest(modo=modo, conteudo_base="base", dados_hunter=payload)
        cabecalhos.add(engine.compor_instrucao_retorica(req).splitlines()[0])
    assert len(cabecalhos) == len(ModoRedacional)
