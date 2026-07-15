"""Testes do Romaneio de Revisão — composição + endpoint.

Cobertura:
- compor_romaneio: NIVEL 1 (zero falhas) e NIVEL 2 (com condições)
- /draft/llm grava .romaneio.md ao lado da minuta
- GET /user/audits/{id}/romaneio devolve o markdown
- 404 quando audit não é do user
- 404 quando arquivo do romaneio sumiu
"""

from __future__ import annotations

from dataclasses import dataclass

from nexus.auditor.service import (
    AuditorAdversarialReport,
    Finding,
    Severity,
)
from nexus.audits.romaneio import compor_romaneio
from nexus.casos.data import FEITOS
from nexus.quality import GateResult, QualityReport
from tests.conftest import signup_and_login


# ---------- compor_romaneio (unit) ----------


def _quality_perfect() -> QualityReport:
    return QualityReport(score=100, gates=[
        GateResult("fonte_por_fato", True, "ok"),
        GateResult("precedente_do_eixo", True, "ok"),
        GateResult("auditoria_silencio", True, "ok"),
        GateResult("pedido_presente", True, "ok"),
        GateResult("assinatura_tigre", True, "ok"),
    ])


def _quality_falho() -> QualityReport:
    return QualityReport(score=60, gates=[
        GateResult("fonte_por_fato", True, "ok"),
        GateResult("precedente_do_eixo", False, "Precedentes ausentes: ['1.258']"),
        GateResult("auditoria_silencio", False, "Auditoria de Silêncio ausente"),
        GateResult("pedido_presente", True, "ok"),
        GateResult("assinatura_tigre", True, "ok"),
    ])


def _auditor_clean() -> AuditorAdversarialReport:
    return AuditorAdversarialReport(findings=[])


def _auditor_com_findings() -> AuditorAdversarialReport:
    return AuditorAdversarialReport(findings=[
        Finding(
            code="cegueira_deliberada",
            severity=Severity.ALTA,
            description="Fato f1 sem eco substantivo",
            evidence="fato f1: foto isolada",
        ),
        Finding(
            code="citacao_nao_verificada",
            severity=Severity.MEDIA,
            description="Súmula 691 sem fonte ancorada",
            evidence="Súmula 691",
        ),
    ])


def test_compor_nivel_1_quando_tudo_passa():
    md = compor_romaneio(
        audit_id="abc-123",
        feito=FEITOS["Feito-HBM"],
        peca_tipo="HC",
        modelo="claude-opus-4-8",
        quality=_quality_perfect(),
        auditor=_auditor_clean(),
        assertions_falhas=[],
        data_iso="01/06/2026 10:00 UTC",
    )
    assert "[NIVEL 1 — DISPARAR]" in md
    assert "[NIVEL 2" not in md.replace("[NIVEL 2 — CONDICIONADA]` peça", "")
    # Não há seção de condições
    assert "Condições a fechar" not in md


def test_compor_nivel_2_quando_quality_falha():
    md = compor_romaneio(
        audit_id="abc-123",
        feito=FEITOS["Feito-HBM"],
        peca_tipo="HC",
        modelo="claude-opus-4-8",
        quality=_quality_falho(),
        auditor=_auditor_clean(),
        assertions_falhas=[],
        data_iso="01/06/2026 10:00 UTC",
    )
    assert "[NIVEL 2 — CONDICIONADA]" in md
    assert "## STATUS: [NIVEL 2 — CONDICIONADA]" in md
    assert "Condições a fechar" in md
    assert "[QUALITY/precedente_do_eixo]" in md
    assert "[QUALITY/auditoria_silencio]" in md


def test_compor_nivel_2_quando_auditor_alta():
    md = compor_romaneio(
        audit_id="abc-123",
        feito=FEITOS["Feito-HBM"],
        peca_tipo="HC",
        modelo="claude-opus-4-8",
        quality=_quality_perfect(),
        auditor=_auditor_com_findings(),
        assertions_falhas=[],
        data_iso="01/06/2026 10:00 UTC",
    )
    assert "[NIVEL 2 — CONDICIONADA]" in md
    # ALTA vem antes de MEDIA na ordem
    idx_alta = md.find("[AUDITOR/ALTA]")
    idx_media = md.find("[AUDITOR/MEDIA]")
    assert 0 < idx_alta < idx_media


def test_compor_inclui_assertions_falhas():
    md = compor_romaneio(
        audit_id="abc-123",
        feito=FEITOS["Feito-HBM"],
        peca_tipo="HC",
        modelo="claude-opus-4-8",
        quality=_quality_perfect(),
        auditor=_auditor_clean(),
        assertions_falhas=["Tema 1.258 não citado", "HC 598.887 ausente"],
        data_iso="01/06/2026 10:00 UTC",
    )
    assert "[NIVEL 2 — CONDICIONADA]" in md
    assert "[ASSERTION] Tema 1.258 não citado" in md
    assert "[ASSERTION] HC 598.887 ausente" in md


def test_compor_inclui_fontes_silenciadas():
    md = compor_romaneio(
        audit_id="abc-123",
        feito=FEITOS["Feito-HBM"],  # tem 4 fontes_silenciadas (commit d19a90e)
        peca_tipo="HC",
        modelo="claude-opus-4-8",
        quality=_quality_perfect(),
        auditor=_auditor_clean(),
        assertions_falhas=[],
        data_iso="01/06/2026 10:00 UTC",
    )
    assert "Auditoria de Silêncio" in md
    assert "Termo formal de reconhecimento" in md


def test_compor_inclui_metadados_do_feito():
    md = compor_romaneio(
        audit_id="abc-123",
        feito=FEITOS["Feito-HBM"],
        peca_tipo="HC",
        modelo="claude-opus-4-8",
        quality=_quality_perfect(),
        auditor=_auditor_clean(),
        assertions_falhas=[],
        data_iso="01/06/2026 10:00 UTC",
    )
    assert "Feito-HBM" in md
    assert "Reconhecimento fotográfico" in md  # quadrante
    assert "Tema 1.258/STF" in md  # eixo
    assert "STJ — Sexta Turma" in md  # tribunal_destino (commit 0c3cad6)
    assert "HC" in md  # peca_alvo (commit a09cfa5)


def test_compor_registra_modo_redacional():
    md = compor_romaneio(
        audit_id="abc-123",
        feito=FEITOS["Feito-HBM"],
        peca_tipo="RHC",
        modelo="claude-opus-4-8",
        quality=_quality_perfect(),
        auditor=_auditor_clean(),
        assertions_falhas=[],
        data_iso="01/06/2026 10:00 UTC",
        modo_redacional="PREQUESTIONADOR",
    )
    assert "**Modo redacional:** PREQUESTIONADOR" in md


def test_compor_modo_redacional_default_pertinaz():
    md = compor_romaneio(
        audit_id="abc-123",
        feito=FEITOS["Feito-HBM"],
        peca_tipo="HC",
        modelo="claude-opus-4-8",
        quality=_quality_perfect(),
        auditor=_auditor_clean(),
        assertions_falhas=[],
        data_iso="01/06/2026 10:00 UTC",
    )
    assert "**Modo redacional:** PERTINAZ" in md


# ---------- /draft/llm gera .romaneio.md no disco ----------


@dataclass
class _FakeMinuta:
    texto: str = "Excelentíssimo Senhor Juiz. minuta de teste"
    modelo: str = "mock-model"
    input_tokens: int = 100
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    output_tokens: int = 50


def _payload() -> dict:
    return {
        "feito_id": "Feito-HBM",
        "peca_tipo": "HC",
        "fatos": [
            {
                "id": "f1",
                "proposto": "X",
                "verificado": "X confirmado",
                "fonte": {"uri": "certidao://feito-hbm/fls-1"},
            }
        ],
    }


def _mock_llm(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    import nexus.llm
    import nexus.quality
    monkeypatch.setattr(nexus.llm, "gerar_minuta", lambda *a, **kw: _FakeMinuta())
    monkeypatch.setattr(
        nexus.quality, "avaliar_qualidade",
        lambda *a, **kw: QualityReport(score=80, gates=[GateResult("g", True, "ok")]),
    )
    monkeypatch.setattr(nexus.llm, "validar_feito_hbm", lambda texto: [])


async def test_draft_llm_grava_romaneio_em_disco(client, monkeypatch, tmp_path):
    _mock_llm(monkeypatch)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    user, token = signup_and_login(client)

    r = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token}"},
        json=_payload(),
    )
    assert r.status_code == 200
    audit_id = r.json()["audit_id"]

    romaneio_path = tmp_path / user["id"] / "audits" / f"{audit_id}.romaneio.md"
    assert romaneio_path.exists()
    conteudo = romaneio_path.read_text(encoding="utf-8")
    assert "ROMANEIO DE REVISÃO" in conteudo
    assert "Feito-HBM" in conteudo


# ---------- GET /user/audits/{id}/romaneio ----------


async def test_get_romaneio_devolve_markdown(client, monkeypatch, tmp_path):
    _mock_llm(monkeypatch)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    _, token = signup_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    gen = client.post("/draft/llm", headers=headers, json=_payload())
    audit_id = gen.json()["audit_id"]

    r = client.get(f"/user/audits/{audit_id}/romaneio", headers=headers)
    assert r.status_code == 200
    assert "text/markdown" in r.headers["content-type"]
    assert "ROMANEIO DE REVISÃO" in r.text
    assert "[NIVEL" in r.text  # status


async def test_get_romaneio_sem_jwt_401(client):
    r = client.get("/user/audits/qualquer/romaneio")
    assert r.status_code == 401


async def test_get_romaneio_de_outro_user_404(client, monkeypatch, tmp_path):
    """Isolamento: user_a não acessa romaneio de user_b. 404 (não 403)."""
    _mock_llm(monkeypatch)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    _, token_a = signup_and_login(client, email="a@x.com")
    _, token_b = signup_and_login(client, email="b@x.com")

    gen = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token_b}"},
        json=_payload(),
    )
    audit_id_b = gen.json()["audit_id"]

    r = client.get(
        f"/user/audits/{audit_id_b}/romaneio",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 404


async def test_get_romaneio_inexistente_404(client):
    _, token = signup_and_login(client)
    r = client.get(
        "/user/audits/nao-existe/romaneio",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


async def test_get_romaneio_arquivo_apagado_404(client, monkeypatch, tmp_path):
    _mock_llm(monkeypatch)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    user, token = signup_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    gen = client.post("/draft/llm", headers=headers, json=_payload())
    audit_id = gen.json()["audit_id"]

    # Apaga manualmente o arquivo do romaneio
    (tmp_path / user["id"] / "audits" / f"{audit_id}.romaneio.md").unlink()

    r = client.get(f"/user/audits/{audit_id}/romaneio", headers=headers)
    assert r.status_code == 404
