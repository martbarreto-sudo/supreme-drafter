"""Testes de integração do gateway /draft/llm (FastAPI TestClient, Zero-Credencial).

Certificam que o barramento barra requisições espúrias (HTTP 422 nativo) e aceita
payloads legítimos — sem qualquer chamada de rede ao provedor LLM.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from deep_hunter.api import app

client = TestClient(app)

_HUNTER_OK = {
    "npu": "0001258-15.2026.8.17.4002",
    "tribunal": "TJPE",
    "orgao_julgador": "Vara Criminal",
}
_PAYLOAD_OK = {
    "modo": "CUSTODIA",
    "conteudo_base": "Fato líquido do caso.",
    "dados_hunter": _HUNTER_OK,
}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["tier"] == 0


def test_aceita_payload_legitimo():
    r = client.post("/draft/llm", json=_PAYLOAD_OK)
    assert r.status_code == 200
    body = r.json()
    assert body["modo"] == "CUSTODIA"
    assert body["npu"] == _HUNTER_OK["npu"]
    assert "[DIRETRIZ RETÓRICA - MODO CUSTODIA]" in body["instrucao_retorica"]


def test_barra_npu_fora_do_padrao_cnj():
    ruim = {**_PAYLOAD_OK, "dados_hunter": {**_HUNTER_OK, "npu": "NPU-INVALIDO-123"}}
    r = client.post("/draft/llm", json=ruim)
    assert r.status_code == 422


def test_barra_modo_redacional_invalido():
    ruim = {**_PAYLOAD_OK, "modo": "MODO_FANTASMA"}
    r = client.post("/draft/llm", json=ruim)
    assert r.status_code == 422


def test_barra_conteudo_base_ausente():
    ruim = {"modo": "PERTINAZ", "dados_hunter": _HUNTER_OK}
    r = client.post("/draft/llm", json=ruim)
    assert r.status_code == 422


def test_barra_dados_hunter_ausente():
    ruim = {"modo": "PERTINAZ", "conteudo_base": "x"}
    r = client.post("/draft/llm", json=ruim)
    assert r.status_code == 422
