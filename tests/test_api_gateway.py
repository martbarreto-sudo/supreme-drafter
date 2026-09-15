"""Testes de integração do gateway /draft/llm (FastAPI TestClient, Zero-Credencial).

Certificam que o barramento barra requisições espúrias (HTTP 422 nativo) e aceita
payloads legítimos — sem qualquer chamada de rede ao provedor LLM.
"""

from __future__ import annotations

from conftest import build_pdf
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


# ── /audit (auditor mock local, Zero-Credencial) ─────────────────────────────

# PDF válido com termos que zeram omissões (hash/plenario/portaria/contemporaneidade).
_PDF_COM_TERMOS = (
    b"%PDF-1.4\n"
    b"laudo com hash sha-256 verificado; ata de plenario juntada; "
    b"portaria de designacao extraordinaria; analise de contemporaneidade da preventiva.\n"
    b"%%EOF\n"
)
# PDF válido "seco" (sem termos) → omissões e quebra de custódia sinalizadas.
_PDF_SECO = b"%PDF-1.4\n%%EOF\n"


def test_audit_aceita_pdf_valido_e_sinaliza_por_texto():
    r = client.post("/audit", files={"file": ("autos.pdf", _PDF_COM_TERMOS, "application/pdf")})
    assert r.status_code == 200
    d = r.json()
    # Contrato aderente ao DossierHunterSchema:
    assert d["npu"].endswith(".2026.8.17." + d["npu"][-4:])
    assert len(d["linha_tempo_atos"]) == 3
    # Termos presentes → sem quebra de custódia e sem omissões.
    assert d["auditoria_custodia"][0]["possui_quebra_custodia"] is False
    assert d["omissao_analise_contemporaneidade"] is False
    assert d["ausencia_ata_plenario"] is False
    assert d["auditoria_magistrados"][0]["possui_desvio"] is True  # portaria => desvio


def test_audit_pdf_seco_sinaliza_omissoes():
    r = client.post("/audit", files={"file": ("autos.pdf", _PDF_SECO, "application/pdf")})
    assert r.status_code == 200
    d = r.json()
    assert d["auditoria_custodia"][0]["possui_quebra_custodia"] is True
    assert d["omissao_analise_contemporaneidade"] is True
    assert d["ausencia_ata_plenario"] is True


def test_audit_barra_pdf_corrompido():
    r = client.post("/audit", files={"file": ("x.pdf", b"nao eh pdf", "application/pdf")})
    assert r.status_code == 422


def test_audit_barra_pdf_vazio():
    r = client.post("/audit", files={"file": ("x.pdf", b"", "application/pdf")})
    assert r.status_code == 422


def test_audit_e_deterministico():
    r1 = client.post("/audit", files={"file": ("a.pdf", _PDF_COM_TERMOS, "application/pdf")})
    r2 = client.post("/audit", files={"file": ("a.pdf", _PDF_COM_TERMOS, "application/pdf")})
    assert r1.json() == r2.json()


def test_ciclo_completo_audit_para_draft():
    """PDF → /audit → DossierHunterSchema → /draft/llm → instrução retórica."""
    a = client.post("/audit", files={"file": ("autos.pdf", _PDF_COM_TERMOS, "application/pdf")})
    assert a.status_code == 200
    dossie = a.json()

    d = client.post(
        "/draft/llm",
        json={"modo": "NULIDADE", "conteudo_base": "sintese", "dados_hunter": dossie},
    )
    assert d.status_code == 200
    assert d.json()["npu"] == dossie["npu"]
    assert "[DIRETRIZ RETÓRICA - MODO NULIDADE]" in d.json()["instrucao_retorica"]


def test_audit_le_pdf_realista_com_stream_comprimido():
    """Regressão de ponta a ponta: num PDF real o texto vive num stream comprimido.

    Enquanto a varredura era feita sobre os bytes crus, estes autos — que trazem
    hash, ata e portaria — voltavam do gateway com todas as omissões sinalizadas.
    """
    pdf = build_pdf(
        b"BT (laudo com hash sha-256 verificado; ata de plenario juntada; portaria de "
        b"designacao; analise de contemporaneidade da preventiva) Tj ET"
    )
    r = client.post("/audit", files={"file": ("autos.pdf", pdf, "application/pdf")})
    assert r.status_code == 200
    d = r.json()
    assert d["auditoria_custodia"][0]["possui_quebra_custodia"] is False
    assert d["omissao_analise_contemporaneidade"] is False
    assert d["ausencia_ata_plenario"] is False

    # E o dossiê resultante continua a servir o /draft/llm sem retoques.
    draft = client.post(
        "/draft/llm",
        json={"modo": "CUSTODIA", "conteudo_base": "sintese", "dados_hunter": d},
    )
    assert draft.status_code == 200
    assert draft.json()["npu"] == d["npu"]


def test_audit_barra_upload_acima_do_teto(monkeypatch):
    """Sem teto, `await file.read()` trazia o upload inteiro para memória."""
    from deep_hunter import api as api_mod

    monkeypatch.setattr(api_mod, "MAX_UPLOAD_BYTES", 1024)
    grande = b"%PDF-1.4\n" + b"0" * 4096
    r = client.post("/audit", files={"file": ("autos.pdf", grande, "application/pdf")})
    assert r.status_code == 413
    assert "teto" in r.json()["detail"]


def test_audit_aceita_upload_dentro_do_teto(monkeypatch):
    from deep_hunter import api as api_mod

    monkeypatch.setattr(api_mod, "MAX_UPLOAD_BYTES", 1 << 20)
    r = client.post("/audit", files={"file": ("autos.pdf", _PDF_COM_TERMOS, "application/pdf")})
    assert r.status_code == 200
