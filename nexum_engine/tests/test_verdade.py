"""Loop de verdade: normalização, fontes (JSON e Supabase) e auditor de citações.

Fixtures reproduzem o formato real da base MINDJUS — incluindo um precedente
FABRICADO em quarentena (o HC 612.234/RJ, raiz histórica da contaminação
sanada no warroom-tigre), que jamais pode voltar a ser citável.
"""

import asyncio
import json

import pytest

from nexum_engine.verdade import (
    FonteDePrecedentes,
    FonteJsonVerificada,
    FonteSupabase,
    Precedente,
    auditar_citacoes,
    extrair_citacoes,
    normalizar_citacao,
)


def executar(coro):
    return asyncio.run(coro)


BASE_FIXTURE = {
    "tema": "cadeia de custódia",
    "atualizado_em": "2026-06-11",
    "precedentes": [
        {
            "numero": "HC 598.051/SP",
            "relator": "Min. Rogério Schietti Cruz",
            "data_julgamento": "2021-03-03",
            "ementa": "BUSCA DOMICILIAR. CONSENTIMENTO DO MORADOR...",
            "tese": "O ônus de comprovar a voluntariedade do consentimento é do Estado.",
            "resultado": "Ordem concedida",
            "tags": ["nulidade", "busca_apreensao"],
            "relevancia": "alta",
            "fonte_verificacao": "STJ — HC 598.051/SP, 6ª Turma",
        },
        {
            "numero": "Súmula 444/STJ",
            "tese": "É vedada a utilização de inquéritos e ações em curso para agravar a pena-base.",
            "tags": ["dosimetria"],
            "fonte_verificacao": "STJ — Súmula 444",
        },
        {
            # Fabricado pelo Manus-stub; saneado e mantido em quarentena.
            "numero": "HC 612.234/RJ",
            "tese": "tese fabricada",
            "tags": ["nulidade"],
            "fonte_verificacao": "",
            "verificacao_pendente": True,
            "motivo_quarentena": "emitido por stub; inexistente em fonte oficial",
        },
    ],
}


@pytest.fixture
def fonte_json(tmp_path):
    (tmp_path / "03_cadeia_custodia.json").write_text(
        json.dumps(BASE_FIXTURE, ensure_ascii=False), encoding="utf-8"
    )
    return FonteJsonVerificada(tmp_path)


# --- normalização ------------------------------------------------------------

def test_normalizacao_ignora_pontos_de_milhar_e_caixa():
    assert normalizar_citacao("hc 598.051/sp") == "HC 598051/SP"
    assert normalizar_citacao("HC 598051/SP") == "HC 598051/SP"
    assert normalizar_citacao("Súmula 444/STJ") == "SUMULA 444/STJ"


# --- extração de citações ------------------------------------------------------

def test_extrai_classes_processuais_sumulas_e_temas():
    texto = (
        "Nos termos do HC 598.051/SP e do RHC 234642/PE, bem como da "
        "Súmula 444 do STJ e do Tema 280, requer-se..."
    )
    assert extrair_citacoes(texto) == [
        "HC 598.051/SP",
        "RHC 234642/PE",
        "Súmula 444/STJ",
        "Tema 280",
    ]


def test_extracao_deduplica_por_forma_normalizada():
    texto = "O HC 598.051/SP... como visto no hc 598051/sp..."
    assert extrair_citacoes(texto) == ["HC 598.051/SP"]


def test_texto_sem_citacoes():
    assert extrair_citacoes("alegações finais sem jurisprudência") == []


# --- FonteJsonVerificada -------------------------------------------------------

def test_fonte_json_carrega_somente_citaveis(fonte_json):
    # 3 registros no arquivo; o fabricado em quarentena fica invisível.
    assert fonte_json.total_citaveis == 2


def test_fonte_json_busca_normalizada(fonte_json):
    p = executar(fonte_json.obter_por_numero("hc 598051/sp"))
    assert p is not None and p.relator == "Min. Rogério Schietti Cruz"
    assert p.tema == "cadeia de custódia"


def test_fonte_json_nunca_devolve_quarentenado(fonte_json):
    assert executar(fonte_json.obter_por_numero("HC 612.234/RJ")) is None


def test_fonte_json_busca_por_tags(fonte_json):
    achados = executar(fonte_json.buscar_por_tags(["dosimetria", "inexistente"]))
    assert [p.numero for p in achados] == ["Súmula 444/STJ"]
    assert executar(fonte_json.buscar_por_tags([])) == []


def test_fonte_json_satisfaz_o_contrato(fonte_json):
    assert isinstance(fonte_json, FonteDePrecedentes)


def test_fonte_json_diretorio_inexistente():
    with pytest.raises(FileNotFoundError):
        FonteJsonVerificada("/caminho/que/nao/existe")


# --- FonteSupabase --------------------------------------------------------------

class FakeDB:
    """DatabasePort falso que devolve linhas pré-armadas e grava as consultas."""

    def __init__(self, linha=None, linhas=()):
        self.linha = linha
        self.linhas = list(linhas)
        self.consultas = []

    async def fetch(self, query, *args):
        self.consultas.append((query, args))
        return self.linhas

    async def fetchrow(self, query, *args):
        self.consultas.append((query, args))
        return self.linha

    async def execute(self, query, *args):
        raise AssertionError("a fonte de leitura nunca deve escrever")


LINHA_HC = {
    "numero": "HC 598.051/SP",
    "tese": "ônus do Estado",
    "tribunal": "STJ",
    "relator": "Min. Rogério Schietti Cruz",
    "data_julgamento": "2021-03-03",
    "ementa": "...",
    "resultado": "Ordem concedida",
    "tags": ["nulidade"],
    "relevancia": "alta",
    "fonte_verificacao": "STJ — HC 598.051/SP",
    "tema": "cadeia de custódia",
    "verificacao_pendente": False,
    "motivo_quarentena": "",
}


def test_fonte_supabase_normaliza_e_filtra_citabilidade_no_sql():
    db = FakeDB(linha=LINHA_HC)
    fonte = FonteSupabase(db)
    p = executar(fonte.obter_por_numero("hc 598.051/sp"))
    assert isinstance(p, Precedente) and p.tribunal == "STJ"
    query, args = db.consultas[0]
    assert args == ("HC 598051/SP",)
    assert "NOT verificacao_pendente" in query
    assert "fonte_verificacao <> ''" in query


def test_fonte_supabase_busca_por_tags_em_minusculas():
    db = FakeDB(linhas=[LINHA_HC])
    achados = executar(FonteSupabase(db).buscar_por_tags(["Nulidade "]))
    assert len(achados) == 1
    _, args = db.consultas[0]
    assert args == (["nulidade"],)


def test_fonte_supabase_satisfaz_o_contrato():
    assert isinstance(FonteSupabase(FakeDB()), FonteDePrecedentes)


# --- auditor ---------------------------------------------------------------------

MINUTA_LIMPA = (
    "A quebra da cadeia de custódia, nos moldes do HC 598.051/SP, "
    "impõe a absolvição; incide ainda a Súmula 444/STJ."
)
MINUTA_CONTAMINADA = (
    MINUTA_LIMPA + " Ademais, conforme assentado no HC 612.234/RJ..."
)


def test_minuta_com_citacoes_verificadas_e_protocolavel(fonte_json):
    relatorio = executar(auditar_citacoes(MINUTA_LIMPA, fonte_json))
    assert relatorio.protocolavel
    assert relatorio.veredito == "PROTOCOLAVEL"
    assert all(c.precedente is not None for c in relatorio.citacoes)


def test_citacao_fabricada_bloqueia_a_peca(fonte_json):
    relatorio = executar(auditar_citacoes(MINUTA_CONTAMINADA, fonte_json))
    assert not relatorio.protocolavel
    assert relatorio.veredito == "NAO_PROTOCOLAVEL"
    assert [c.citacao for c in relatorio.nao_verificadas] == ["HC 612.234/RJ"]


def test_minuta_sem_citacoes_e_protocolavel(fonte_json):
    relatorio = executar(auditar_citacoes("sem jurisprudência", fonte_json))
    assert relatorio.protocolavel and relatorio.citacoes == ()


def test_fonte_do_arquivo_e_herdada_pelo_registro(tmp_path):
    base = {
        "tema": "reconhecimento",
        "fonte_verificacao": "STJ — verificado em fonte oficial (arquivo)",
        "precedentes": [
            {"numero": "HC 712.781/RJ", "tese": "t", "tags": []},
            {
                "numero": "HC 000.000/XX",
                "tese": "fabricado",
                "verificacao_pendente": True,
                "motivo_quarentena": "stub",
            },
        ],
    }
    (tmp_path / "07_reconhecimento.json").write_text(
        json.dumps(base, ensure_ascii=False), encoding="utf-8"
    )
    fonte = FonteJsonVerificada(tmp_path)
    p = executar(fonte.obter_por_numero("HC 712781/RJ"))
    assert p is not None
    assert p.fonte_verificacao.endswith("(arquivo)")
    # A herança da fonte NÃO tira ninguém da quarentena.
    assert executar(fonte.obter_por_numero("HC 000.000/XX")) is None
