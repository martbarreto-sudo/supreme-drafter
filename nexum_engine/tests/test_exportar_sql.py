"""Gerador de carga MINDJUS → SQL: quarentena antecipada, dedupe e escaping."""

import json

import pytest

from nexum_engine.verdade.exportar_sql import MOTIVO_SEM_FONTE, gerar_sql, main

ARQ_A = {
    "tema": "cadeia de custódia",
    "precedentes": [
        {
            "numero": "HC 598.051/SP",
            "tese": "o ônus é do Estado ('fruits of the poisonous tree')",
            "tags": ["nulidade"],
            "fonte_verificacao": "STJ — HC 598.051/SP",
        },
        {
            "numero": "HC 612.234/RJ",
            "tese": "fabricada",
            "verificacao_pendente": True,
            "motivo_quarentena": "emitido por stub",
        },
    ],
}
ARQ_B = {
    "tema": "provas ilícitas",
    "precedentes": [
        # Duplicata do citável, com tag nova e sem pontuação no número.
        {
            "numero": "HC 598051/SP",
            "tese": "duplicata",
            "tags": ["prova_ilicita"],
            "fonte_verificacao": "STJ",
        },
        # Órfão: legítimo, mas sem fonte registrada.
        {"numero": "Súmula 444/STJ", "tese": "veda maus antecedentes por inquéritos"},
    ],
}


@pytest.fixture
def sql(tmp_path):
    (tmp_path / "01_a.json").write_text(json.dumps(ARQ_A, ensure_ascii=False), "utf-8")
    (tmp_path / "02_b.json").write_text(json.dumps(ARQ_B, ensure_ascii=False), "utf-8")
    return gerar_sql(tmp_path)


def test_manifesto_e_transacional_e_idempotente(sql):
    assert sql.strip().startswith("-- Manifesto")
    assert "BEGIN;" in sql and sql.strip().endswith("COMMIT;")
    assert sql.count("ON CONFLICT (numero_normalizado) DO NOTHING") == 3


def test_dedupe_por_numero_normalizado_com_uniao_de_tags(sql):
    # HC 598.051/SP e HC 598051/SP viram UMA linha, com as duas tags.
    assert sql.count("'HC 598051/SP'") == 1
    assert "ARRAY['nulidade', 'prova_ilicita']::text[]" in sql


def test_orfao_sem_fonte_entra_quarentenado(sql):
    linha = [l for l in sql.split("INSERT") if "SUMULA 444/STJ" in l][0]
    assert "TRUE" in linha
    assert MOTIVO_SEM_FONTE.split("—")[0].strip() in linha


def test_fabricado_mantem_quarentena_e_motivo_original(sql):
    linha = [l for l in sql.split("INSERT") if "HC 612234/RJ" in l][0]
    assert "TRUE" in linha and "emitido por stub" in linha


def test_citavel_sai_sem_quarentena(sql):
    linha = [l for l in sql.split("INSERT") if "'HC 598051/SP'" in l][0]
    assert "FALSE, ''" in linha


def test_aspas_simples_escapadas(sql):
    assert "(''fruits of the poisonous tree'')" in sql


def test_toda_linha_exportada_respeita_os_checks_do_ddl(tmp_path):
    """Invariantes dos CHECKs, verificados nos objetos que viram INSERT:
    fonte_ou_quarentena (fonte <> '' OU pendente) e quarentena_motivada
    (pendente => motivo <> '')."""
    from nexum_engine.verdade.exportar_sql import (
        _carregar_todos,
        _deduplicar,
        _quarentenar_orfao,
    )

    (tmp_path / "01_a.json").write_text(json.dumps(ARQ_A, ensure_ascii=False), "utf-8")
    (tmp_path / "02_b.json").write_text(json.dumps(ARQ_B, ensure_ascii=False), "utf-8")
    exportados = _deduplicar(
        [_quarentenar_orfao(p) for p in _carregar_todos(tmp_path)]
    )
    assert exportados, "fixture não pode gerar manifesto vazio"
    for p in exportados:
        assert p.fonte_verificacao or p.verificacao_pendente, p.numero
        assert not p.verificacao_pendente or p.motivo_quarentena, p.numero


def test_diretorio_inexistente():
    with pytest.raises(FileNotFoundError):
        gerar_sql("/nao/existe")


def test_cli_gera_arquivo(tmp_path, capsys):
    (tmp_path / "01_a.json").write_text(json.dumps(ARQ_A, ensure_ascii=False), "utf-8")
    saida = tmp_path / "seed.sql"
    assert main([str(tmp_path), "-o", str(saida)]) == 0
    assert saida.read_text(encoding="utf-8").strip().endswith("COMMIT;")
