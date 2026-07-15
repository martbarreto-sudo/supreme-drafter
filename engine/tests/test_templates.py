"""Templates determinísticos Jinja2 — RHC, RCL, EDcl (item 3 do plano de portagem).

Cobertura via rota POST /draft (sem LLM, sem cobrança): HALT continua
soberano, cada template renderiza sua estrutura canônica, e a Auditoria de
Silêncio puxa fontes_silenciadas do Feito. Dados sintéticos, rede isolada.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from nexus.api import app

client = TestClient(app)


def _payload(peca_tipo: str) -> dict:
    return {
        "feito_id": "Feito-HBM",
        "peca_tipo": peca_tipo,
        "fatos": [
            {
                "id": "f1",
                "proposto": "Reconhecimento por foto",
                "verificado": "Reconhecimento por foto isolada, sem fila, sem termo",
                "fonte": {"uri": "certidao://feito-hbm/fls-12"},
            }
        ],
    }


@pytest.mark.parametrize("peca_tipo", ["RHC", "RCL", "EDCL"])
def test_template_renderiza_estrutura_comum(peca_tipo):
    r = client.post("/draft", json=_payload(peca_tipo))
    assert r.status_code == 200
    body = r.json()
    assert body["halt"] is False
    texto = body["texto"]
    # cabeçalho e blocos comuns a todas as fôrmas
    assert "Feito-HBM" in texto
    assert "MATRIZ DE VULNERABILIDADES" in texto
    assert "AUDITORIA DE SILÊNCIO" in texto
    # fato líquido e fonte primária impressos
    assert "certidao://feito-hbm/fls-12" in texto
    # tribunal_destino do Feito-HBM entra no endereçamento
    assert "STJ — Sexta Turma" in texto
    # Auditoria de Silêncio puxa as fontes_silenciadas do Feito
    assert "art. 226" in texto


def test_rhc_foco_confiabilidade_da_prova():
    texto = client.post("/draft", json=_payload("RHC")).json()["texto"]
    assert "RECURSO ORDINÁRIO EM HABEAS CORPUS" in texto
    assert "QUEBRA DE CONFIABILIDADE DA PROVA" in texto
    assert "cadeia de custódia" in texto


def test_rcl_foco_tese_vinculante_e_juiz_natural():
    texto = client.post("/draft", json=_payload("RCL")).json()["texto"]
    assert "RECLAMAÇÃO CONSTITUCIONAL" in texto
    assert "juiz natural" in texto.lower()
    assert "ato reclamado" in texto.lower()


def test_edcl_foco_omissao_e_prequestionamento():
    texto = client.post("/draft", json=_payload("EDCL")).json()["texto"]
    assert "EMBARGOS DE DECLARAÇÃO" in texto
    assert "OMISSÃO" in texto
    assert "PREQUESTIONAMENTO" in texto
    assert "art. 619" in texto  # base legal dos embargos no CPP


@pytest.mark.parametrize("peca_tipo", ["RHC", "RCL", "EDCL"])
def test_template_halt_sem_fonte(peca_tipo):
    """HALT é soberano: fato dispositivo sem fonte bloqueia qualquer fôrma."""
    r = client.post(
        "/draft",
        json={
            "feito_id": "Feito-HBM",
            "peca_tipo": peca_tipo,
            "fatos": [{"id": "f1", "proposto": "X aconteceu"}],
        },
    )
    assert r.status_code == 422
    assert r.json()["halt"] is True
