# -*- coding: utf-8 -*-
"""
Suíte de testes do orquestrador de peer-review NEXUM TIER 0.

Cobertura-alvo do gate TIER 0: >= 90%. Nenhum teste depende de rede — os
clientes de API (Anthropic / gemini-cli) são injetados como dublês
determinísticos. Execução:

    python -m pytest tests/ -v --cov=. --cov-report=term-missing
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Garante import do módulo a partir do diretório .github/scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import peer_review_orchestrator as orq  # noqa: E402


# --------------------------------------------------------------------------- #
# Fixtures — JSONs de revisão sintéticos conformes ao schema
# --------------------------------------------------------------------------- #


@pytest.fixture
def rev_aprovado_claude() -> dict:
    return {
        "tipo_peca": "agravo_regimental",
        "risco_rejeicao": 12,
        "vicios_formais": ["fundamentacao_deficiente"],
        "preliminares_ausentes": [],
        "fundamentos_fragilizados": [],
        "jurisprudencia_omitida": ["HC 598.051/SP"],
        "veredito_tier0": "aprovado_>=97",
        "score": 98,
        "recomendacoes": ["reforçar tese de ilicitude da prova"],
    }


@pytest.fixture
def rev_aprovado_gemini() -> dict:
    return {
        "tipo_peca": "agravo_regimental",
        "risco_rejeicao": 18,
        "vicios_formais": ["fundamentacao_deficiente"],
        "preliminares_ausentes": [],
        "fundamentos_fragilizados": [],
        "jurisprudencia_omitida": ["Tema 990/STF"],
        "veredito_tier0": "aprovado_>=97",
        "score": 97,
        "recomendacoes": [],
    }


@pytest.fixture
def rev_reprovado() -> dict:
    return {
        "tipo_peca": "habeas_corpus",
        "risco_rejeicao": 70,
        "vicios_formais": ["intempestividade"],
        "preliminares_ausentes": ["tempestividade"],
        "fundamentos_fragilizados": ["nexo causal"],
        "jurisprudencia_omitida": [],
        "veredito_tier0": "reprovado_<97",
        "score": 60,
        "recomendacoes": ["sanar tempestividade"],
    }


# --------------------------------------------------------------------------- #
# 1-3. LGPDAnonimizer
# --------------------------------------------------------------------------- #


def test_lgpd_mascara_cpf_telefone_email():
    anon = orq.LGPDAnonimizer()
    texto = "Réu CPF 123.456.789-00, fone (81) 99876-5432, email reu@exemplo.com"
    out = anon.anonimizar(texto)
    assert "123.456.789-00" not in out
    assert "[CPF_MASCARADO]" in out
    assert "[EMAIL_MASCARADO]" in out
    assert "[TELEFONE_MASCARADO]" in out


def test_lgpd_preserva_oab_socios_rt():
    anon = orq.LGPDAnonimizer()
    texto = "Dr. Marcelo OAB/PE 27.543 e Dr. Ydigoras OAB/PE 27.482 assinam."
    out = anon.anonimizar(texto)
    assert "OAB/PE 27.543" in out
    assert "OAB/PE 27.482" in out
    assert "[OAB_MASCARADA]" not in out


def test_lgpd_mascara_oab_de_terceiros():
    anon = orq.LGPDAnonimizer()
    texto = "Advogado da outra parte OAB/SP 99.111 ingressou nos autos."
    out = anon.anonimizar(texto)
    assert "OAB/SP 99.111" not in out
    assert "[OAB_MASCARADA]" in out


def test_lgpd_texto_vazio_e_contem_dado_sensivel():
    anon = orq.LGPDAnonimizer()
    assert anon.anonimizar("") == ""
    assert anon.contem_dado_sensivel("CPF 123.456.789-00") is True
    assert anon.contem_dado_sensivel("texto limpo sem dados") is False


# --------------------------------------------------------------------------- #
# 4. PecaExtractor (extrator injetado — sem PDF real)
# --------------------------------------------------------------------------- #


def test_peca_extractor_com_injecao():
    extrator = orq.PecaExtractor(extractor=lambda caminho: f"TEXTO de {caminho}")
    assert extrator.extrair_texto("pecas/hc.pdf") == "TEXTO de pecas/hc.pdf"


# --------------------------------------------------------------------------- #
# 5-7. Roteamento PDF / código
# --------------------------------------------------------------------------- #


def test_roteamento_pipeline_juridico():
    rot = orq.rotear_arquivos(["pecas/hc_001.pdf", "README.md"])
    assert rot.roda_pipeline_juridico is True
    assert rot.roda_pipeline_codigo is False
    assert rot.pdfs_pecas == ["pecas/hc_001.pdf"]


def test_roteamento_pipeline_codigo():
    rot = orq.rotear_arquivos(["engine/gerador.py", "nexum_engine/validator.py"])
    assert rot.roda_pipeline_codigo is True
    assert rot.roda_pipeline_juridico is False
    assert len(rot.arquivos_codigo) == 2


def test_roteamento_ambos_pipelines_e_ignora_irrelevantes():
    rot = orq.rotear_arquivos(
        ["pecas/ap.pdf", "engine/x.py", "docs/leiame.md", "", "pecas/nota.txt"]
    )
    assert rot.roda_pipeline_juridico is True
    assert rot.roda_pipeline_codigo is True
    assert "pecas/nota.txt" not in rot.pdfs_pecas  # não é .pdf


# --------------------------------------------------------------------------- #
# 8. construir_xml_auditoria — tags semânticas
# --------------------------------------------------------------------------- #


def test_xml_auditoria_usa_tags_semanticas():
    xml = orq.construir_xml_auditoria("PECA ANON", "fatos do caso")
    assert "<auditoria_recursal>" in xml
    assert "<peca_integral_anonimizada>PECA ANON" in xml
    assert "<fatos_relevantes>fatos do caso" in xml
    # Jamais tags genéricas
    assert "<document>" not in xml and "<text>" not in xml


# --------------------------------------------------------------------------- #
# 9-10. ClaudeReviewer (cliente dublê) + pré-fill `{`
# --------------------------------------------------------------------------- #


class _FakeContent:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeResp:
    def __init__(self, text: str) -> None:
        self.content = [_FakeContent(text)]


class _FakeMessages:
    def __init__(self, payload_sem_chave: str) -> None:
        self._payload = payload_sem_chave
        self.ultima_chamada: dict | None = None

    def create(self, **kwargs):
        self.ultima_chamada = kwargs
        return _FakeResp(self._payload)


class _FakeAnthropic:
    def __init__(self, payload_sem_chave: str) -> None:
        self.messages = _FakeMessages(payload_sem_chave)


def test_claude_reviewer_parse_com_prefill(rev_aprovado_claude):
    # O cliente devolve o JSON SEM a chave inicial `{` (pré-fill já a injeta).
    corpo = json.dumps(rev_aprovado_claude, ensure_ascii=False)
    assert corpo.startswith("{")
    payload_sem_chave = corpo[1:]  # remove a `{` inicial
    fake = _FakeAnthropic(payload_sem_chave)
    rev = orq.ClaudeReviewer(client=fake)
    out = rev.revisar("Peça com CPF 111.222.333-44 do réu", contexto="ctx")
    assert out["score"] == 98
    assert out["tipo_peca"] == "agravo_regimental"
    # Verifica que o pré-fill `{` foi enviado no turno do assistant.
    msgs = fake.messages.ultima_chamada["messages"]
    assert msgs[-1] == {"role": "assistant", "content": "{"}
    assert fake.messages.ultima_chamada["temperature"] == 0.0


def test_claude_reviewer_lgpd_aplicada_antes_do_envio():
    fake = _FakeAnthropic('"score": 99}'[:-1] + "}")  # payload mínimo válido p/ parse
    # payload acima não é JSON completo; usamos um válido:
    fake = _FakeAnthropic(json.dumps({"score": 99})[1:])
    rev = orq.ClaudeReviewer(client=fake)
    rev.revisar("CPF do réu 123.456.789-00")
    user_msg = fake.messages.ultima_chamada["messages"][0]["content"]
    assert "123.456.789-00" not in user_msg  # mascarado antes do envio
    assert "[CPF_MASCARADO]" in user_msg


def test_claude_reviewer_json_invalido_levanta():
    fake = _FakeAnthropic("isto nao e json")
    rev = orq.ClaudeReviewer(client=fake)
    with pytest.raises(RuntimeError, match="claude retornou JSON inválido"):
        rev.revisar("peça")


# --------------------------------------------------------------------------- #
# 11-12. GeminiReviewer (runner dublê)
# --------------------------------------------------------------------------- #


def test_gemini_reviewer_extrai_json_com_ruido(rev_aprovado_gemini):
    bloco = json.dumps(rev_aprovado_gemini, ensure_ascii=False)
    saida = "Pensando...\n" + bloco + "\nFim da execução."

    def runner(comando, prompt):
        assert "gemini" in comando[0]
        assert "gemini-3-pro" in comando
        return saida

    rev = orq.GeminiReviewer(runner=runner)
    out = rev.revisar("peça com OAB/PE 27.543 preservada")
    assert out["score"] == 97
    assert out["tipo_peca"] == "agravo_regimental"


def test_gemini_reviewer_sem_json_levanta():
    rev = orq.GeminiReviewer(runner=lambda c, p: "sem json aqui")
    with pytest.raises(RuntimeError, match="não retornou JSON"):
        rev.revisar("peça")


def test_gemini_reviewer_json_corrompido_levanta():
    rev = orq.GeminiReviewer(runner=lambda c, p: "{ score: invalido }")
    with pytest.raises(RuntimeError, match="JSON inválido"):
        rev.revisar("peça")


# --------------------------------------------------------------------------- #
# 13-15. TIER0Consolidator
# --------------------------------------------------------------------------- #


def test_consolidador_aprovado_convergencia(rev_aprovado_claude, rev_aprovado_gemini):
    cons = orq.TIER0Consolidator()
    res = cons.consolidar(rev_aprovado_claude, rev_aprovado_gemini)
    assert res.aprovado is True
    assert res.score_consolidado == pytest.approx(97.5)
    # Vício comum aparece nas convergências
    assert "fundamentacao_deficiente" in res.convergencias
    # Jurisprudência exclusiva de cada modelo
    assert any("598.051" in d for d in res.divergencias_claude)
    assert any("990" in d for d in res.divergencias_gemini)
    assert "TIER 0" in res.markdown


def test_consolidador_reprovado_falha_gate(rev_aprovado_claude, rev_reprovado):
    cons = orq.TIER0Consolidator(gate_score=97)
    res = cons.consolidar(rev_aprovado_claude, rev_reprovado)
    assert res.aprovado is False
    assert res.score_consolidado < 97
    assert "REPROVADO" in res.markdown


def test_consolidador_delta_risco_significativo(rev_aprovado_claude, rev_reprovado):
    cons = orq.TIER0Consolidator()
    res = cons.consolidar(rev_aprovado_claude, rev_reprovado)
    assert res.delta_risco > 15
    assert "Divergência significativa" in res.markdown


def test_consolidador_campos_ausentes_nao_quebram():
    cons = orq.TIER0Consolidator()
    res = cons.consolidar({}, {})
    assert res.score_consolidado == 0.0
    assert res.aprovado is False
    assert res.convergencias == []


# --------------------------------------------------------------------------- #
# 16. render_comentario_provedor
# --------------------------------------------------------------------------- #


def test_render_comentario_provedor_aprovado(rev_aprovado_claude):
    md = orq.render_comentario_provedor("Claude Opus 4.8", "claude-opus-4-8", rev_aprovado_claude)
    assert "APROVADO" in md
    assert "claude-opus-4-8" in md
    assert "```json" in md


def test_render_comentario_provedor_score_invalido():
    md = orq.render_comentario_provedor("Gemini", "gemini-3-pro", {"score": "n/a"})
    assert "REPROVADO" in md


# --------------------------------------------------------------------------- #
# 17. carregar_system_prompt — arquivo versionado existe
# --------------------------------------------------------------------------- #


def test_system_prompt_carrega_arquivo_versionado():
    sp = orq.carregar_system_prompt()
    assert "Ribeiro & Tigre" in sp
    assert "HC 598.051/SP" in sp
    assert "02/03/2021" in sp  # data canônica correta


# --------------------------------------------------------------------------- #
# 18-20. CLI main()
# --------------------------------------------------------------------------- #


def test_cli_rotear(capsys):
    rc = orq.main(["rotear", "--arquivos", "pecas/x.pdf", "engine/y.py"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["roda_pipeline_juridico"] is True
    assert out["roda_pipeline_codigo"] is True


def test_cli_consolidar_aprovado(tmp_path, rev_aprovado_claude, rev_aprovado_gemini):
    pc = tmp_path / "claude.json"
    pg = tmp_path / "gemini.json"
    out = tmp_path / "rel.md"
    pc.write_text(json.dumps(rev_aprovado_claude), encoding="utf-8")
    pg.write_text(json.dumps(rev_aprovado_gemini), encoding="utf-8")
    rc = orq.main(
        ["consolidar", "--claude", str(pc), "--gemini", str(pg), "--out", str(out), "--gate", "97"]
    )
    assert rc == 0
    assert "TIER 0" in out.read_text(encoding="utf-8")


def test_cli_consolidar_reprovado_falha(tmp_path, rev_aprovado_claude, rev_reprovado):
    pc = tmp_path / "c.json"
    pg = tmp_path / "g.json"
    out = tmp_path / "r.md"
    pc.write_text(json.dumps(rev_aprovado_claude), encoding="utf-8")
    pg.write_text(json.dumps(rev_reprovado), encoding="utf-8")
    rc = orq.main(
        ["consolidar", "--claude", str(pc), "--gemini", str(pg), "--out", str(out), "--gate", "97"]
    )
    assert rc == 1  # gate reprovado -> exit code 1 quebra o job
