"""Gate de citações (CLI): postura binária, contingência e códigos de saída."""

import json

import pytest

from nexum_engine.verdade.gate import main

BASE = {
    "tema": "cadeia de custódia",
    "precedentes": [
        {
            "numero": "HC 598.051/SP",
            "tese": "ônus do Estado",
            "fonte_verificacao": "STJ — HC 598.051/SP",
        },
    ],
}


@pytest.fixture
def base_dir(tmp_path):
    d = tmp_path / "mindjus_data"
    d.mkdir()
    (d / "03.json").write_text(json.dumps(BASE, ensure_ascii=False), "utf-8")
    return d


def _peca(tmp_path, nome, texto):
    p = tmp_path / nome
    p.write_text(texto, encoding="utf-8")
    return p


def test_peca_limpa_sai_zero(base_dir, tmp_path, capsys):
    peca = _peca(tmp_path, "minuta.md", "Aplica-se o HC 598.051/SP.")
    assert main([str(peca), "--base", str(base_dir)]) == 0
    saida = capsys.readouterr().out
    assert "GATE APROVADO" in saida and "PROTOCOLAVEL" in saida


def test_citacao_fabricada_derruba_o_pipeline(base_dir, tmp_path, capsys):
    peca = _peca(tmp_path, "minuta.md", "Conforme o HC 612.234/RJ...")
    assert main([str(peca), "--base", str(base_dir)]) == 1
    saida = capsys.readouterr().out
    assert "GATE BLOQUEADO" in saida
    assert "NAO_PROTOCOLAVEL" in saida
    assert "HC 612.234/RJ" in saida


def test_um_arquivo_contaminado_bloqueia_o_lote(base_dir, tmp_path):
    limpa = _peca(tmp_path, "a.md", "HC 598.051/SP")
    suja = _peca(tmp_path, "b.md", "HC 612.234/RJ")
    assert main([str(limpa), str(suja), "--base", str(base_dir)]) == 1


def test_extensao_fora_do_escopo_e_pulada_sem_bloquear(base_dir, tmp_path, capsys):
    pdf = tmp_path / "peca.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    assert main([str(pdf), "--base", str(base_dir)]) == 0
    assert "fora do escopo" in capsys.readouterr().out


def test_base_ausente_em_modo_estrito_sai_dois(tmp_path):
    peca = _peca(tmp_path, "m.md", "x")
    assert main([str(peca), "--base", str(tmp_path / "nao-existe")]) == 2


def test_base_ausente_com_flag_sela_inconclusivo(tmp_path, capsys):
    peca = _peca(tmp_path, "m.md", "HC 612.234/RJ")
    codigo = main([
        str(peca), "--base", str(tmp_path / "nao-existe"),
        "--inconclusivo-sem-base",
    ])
    assert codigo == 0
    saida = capsys.readouterr().out
    assert "GATE INCONCLUSIVO" in saida
    assert "NÃO foram reprovadas" in saida


def test_arquivo_inexistente_sai_dois(base_dir):
    assert main(["/nao/existe.md", "--base", str(base_dir)]) == 2
