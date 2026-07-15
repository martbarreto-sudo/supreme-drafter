# -*- coding: utf-8 -*-
"""Ponte NEXUM (lado supreme-drafter) — verificador determinístico de precedentes.

Espelha as garantias do warroom-tigre (tests/test_ponte_nexum.py):
  1. blocklist de fabricadas sempre detectada, em qualquer grafia;
  2. manifesto vendorizado íntegro (sha256) e sem fabricada como "citável";
  3. fixture cross-repo (arquivo IDÊNTICO nos dois repos) classificada com o
     MESMO resultado — o teste ponta a ponta da ponte;
  4. o gate da consolidação REPROVA com citação fabricada, mesmo com score 100.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Garante import dos módulos a partir do diretório .github/scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import peer_review_orchestrator as orq  # noqa: E402
import verificador_precedentes as vp  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "peca_ponte_nexum.txt"


# --------------------------------------------------------------------------- #
# Blocklist e manifesto vendorizado
# --------------------------------------------------------------------------- #


def test_blocklist_reconhece_fabricadas_em_qualquer_grafia():
    for grafia in ("HC 612.234/RJ", "HC 612234", "REsp 612.234/SP", "HC 587.456/MG"):
        (chave,) = vp.normalizar_citacoes(grafia)
        assert vp.citacao_fabricada(chave), grafia
    assert not vp.citacao_fabricada("HC 598051")


def test_manifesto_vendorizado_integro_e_sem_fabricada():
    m = vp.carregar_manifesto()
    assert vp.manifesto_integro(m), (
        "sha256 do manifesto vendorizado não confere — recopie do warroom-tigre "
        "(python ponte_nexum.py gerar)"
    )
    assert m["schema"] == "nexum-ponte/1"
    assert m["contagens"]["verificadas"] >= 1
    citaveis = set(m["verificadas"]) | set(m["na_base_sem_fonte"])
    for chave in citaveis:
        assert not vp.citacao_fabricada(chave), (
            f"citação fabricada {chave} presente no manifesto como citável"
        )


# --------------------------------------------------------------------------- #
# Fixture cross-repo — MESMAS asserções do lado warroom-tigre
# --------------------------------------------------------------------------- #


def test_fixture_cross_repo_classificacao_estavel():
    resultado = vp.classificar_texto(
        FIXTURE.read_text(encoding="utf-8"), vp.carregar_manifesto()
    )
    assert resultado["fabricadas"] == ["HC 612234"]
    assert "HC 598051" in resultado["verificadas"]
    assert "RE 603616" in resultado["verificadas"]
    citaveis = set(resultado["verificadas"]) | set(resultado["na_base_sem_fonte"])
    assert "SUMULA 444" in citaveis
    assert "RESP 9999999" in resultado["fora_da_base"]
    assert resultado["total_citacoes"] == 7


# --------------------------------------------------------------------------- #
# Pipeline: executar() com rota/texto
# --------------------------------------------------------------------------- #


def test_executar_nao_aplicavel_sem_peca():
    resultado = vp.executar({"roda_pipeline_juridico": False}, None)
    assert resultado["aplicavel"] is False
    assert resultado["fabricadas"] == []


def test_executar_com_texto_direto():
    resultado = vp.executar(None, "Aplica-se o HC 598.051/SP e o HC 612.234/RJ.")
    assert resultado["aplicavel"] is True
    assert resultado["manifesto_integro"] is True
    assert resultado["fabricadas"] == ["HC 612234"]
    assert resultado["verificadas"] == ["HC 598051"]


def test_render_secao_markdown_alerta_fabricada():
    resultado = vp.executar(None, "Cita o HC 612.234/RJ.")
    md = vp.render_secao_markdown(resultado)
    assert "REPROVAÇÃO AUTOMÁTICA" in md
    assert "HC 612234" in md


def test_render_secao_vazia_quando_nao_aplicavel():
    assert vp.render_secao_markdown({"aplicavel": False}) == ""


# --------------------------------------------------------------------------- #
# Gate da consolidação: fabricada reprova mesmo com score 100
# --------------------------------------------------------------------------- #


def _rev_aprovada() -> dict:
    return {
        "tipo_peca": "habeas_corpus",
        "risco_rejeicao": 5,
        "vicios_formais": [],
        "preliminares_ausentes": [],
        "fundamentos_fragilizados": [],
        "jurisprudencia_omitida": [],
        "veredito_tier0": "aprovado_>=97",
        "score": 100,
        "recomendacoes": [],
    }


def _consolidar(tmp_path: Path, verificacao: dict | None) -> tuple[int, str]:
    claude = tmp_path / "claude.json"
    gemini = tmp_path / "gemini.json"
    out = tmp_path / "relatorio.md"
    claude.write_text(json.dumps(_rev_aprovada()), encoding="utf-8")
    gemini.write_text(json.dumps(_rev_aprovada()), encoding="utf-8")
    argv = [
        "consolidar", "--claude", str(claude), "--gemini", str(gemini),
        "--out", str(out), "--gate", "97",
    ]
    if verificacao is not None:
        v = tmp_path / "verificacao.json"
        v.write_text(json.dumps(verificacao, ensure_ascii=False), encoding="utf-8")
        argv += ["--verificacao", str(v)]
    rc = orq.main(argv)
    return rc, out.read_text(encoding="utf-8")


def test_gate_reprova_com_fabricada_mesmo_score_100(tmp_path):
    verificacao = vp.executar(None, "Fundamenta-se no HC 612.234/RJ.")
    rc, md = _consolidar(tmp_path, verificacao)
    assert rc == 1, "citação fabricada tem de reprovar o gate, ainda que score=100"
    assert "REPROVAÇÃO AUTOMÁTICA" in md
    assert "HC 612234" in md


def test_gate_aprova_sem_fabricada_e_anexa_secao(tmp_path):
    verificacao = vp.executar(None, "Aplica-se o HC 598.051/SP.")
    rc, md = _consolidar(tmp_path, verificacao)
    assert rc == 0
    assert "Ponte NEXUM" in md
    assert "HC 598051" in md


def test_gate_tolera_verificacao_ausente(tmp_path):
    rc, md = _consolidar(tmp_path, None)
    assert rc == 0
    assert "Ponte NEXUM" not in md


def test_gate_tolera_verificacao_ilegivel(tmp_path):
    claude = tmp_path / "claude.json"
    gemini = tmp_path / "gemini.json"
    out = tmp_path / "relatorio.md"
    claude.write_text(json.dumps(_rev_aprovada()), encoding="utf-8")
    gemini.write_text(json.dumps(_rev_aprovada()), encoding="utf-8")
    rc = orq.main([
        "consolidar", "--claude", str(claude), "--gemini", str(gemini),
        "--out", str(out), "--gate", "97",
        "--verificacao", str(tmp_path / "nao_existe.json"),
    ])
    assert rc == 0


def test_indisponivel_com_fabricada_reporta_ponte(tmp_path):
    """Peça presente, LLMs não configurados: inconclusivo, mas a ponte fala."""
    indis = {
        "tipo_peca": "indisponivel", "disponivel": False, "risco_rejeicao": 0,
        "vicios_formais": [], "preliminares_ausentes": [],
        "fundamentos_fragilizados": [], "jurisprudencia_omitida": [],
        "veredito_tier0": "inconclusivo", "score": 0, "recomendacoes": [],
    }
    claude = tmp_path / "claude.json"
    gemini = tmp_path / "gemini.json"
    out = tmp_path / "relatorio.md"
    claude.write_text(json.dumps(indis), encoding="utf-8")
    gemini.write_text(json.dumps(indis), encoding="utf-8")
    v = tmp_path / "verificacao.json"
    v.write_text(
        json.dumps(vp.executar(None, "Cita o HC 612.234/RJ."), ensure_ascii=False),
        encoding="utf-8",
    )
    rc = orq.main([
        "consolidar", "--claude", str(claude), "--gemini", str(gemini),
        "--out", str(out), "--gate", "97", "--verificacao", str(v),
    ])
    assert rc == 1
    md = out.read_text(encoding="utf-8")
    assert "REPROVAÇÃO AUTOMÁTICA" in md
