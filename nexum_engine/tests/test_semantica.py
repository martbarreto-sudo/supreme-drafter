"""Fase 2 — busca semântica: contrato, SQL vetorial e fallback honesto."""

import asyncio
import json

import pytest

from nexum_engine.ports import EmbedderPort
from nexum_engine.verdade import FonteDePrecedentes, FonteJsonVerificada, FonteSupabase
from nexum_engine.verdade.fontes import _tokens_de_busca, _vetor_para_sql


def executar(coro):
    return asyncio.run(coro)


DIM = 768


class FakeEmbedder:
    """EmbedderPort falso: vetor estático previsível, zero HTTP."""

    def __init__(self, vetor=None, erro: Exception | None = None):
        self.vetor = vetor or [0.1] * DIM
        self.erro = erro
        self.chamadas: list[list[str]] = []

    async def embed(self, textos):
        if self.erro:
            raise self.erro
        if any(not t for t in textos):
            raise ValueError("texto vazio inválido para embedding")
        self.chamadas.append(list(textos))
        return [self.vetor for _ in textos]


class FakeDB:
    def __init__(self, linhas=(), erro: Exception | None = None):
        self.linhas = list(linhas)
        self.erro = erro
        self.consultas = []

    async def fetch(self, query, *args):
        self.consultas.append((query, args))
        if self.erro and "vetor_semantico" in query:
            raise self.erro
        return self.linhas

    async def fetchrow(self, query, *args):
        raise AssertionError("não usado nestes testes")

    async def execute(self, query, *args):
        raise AssertionError("a fonte de leitura nunca deve escrever")


LINHA = {
    "numero": "HC 598.051/SP",
    "tese": "quebra da cadeia de custódia em espelhamento de WhatsApp",
    "tags": ["nulidade", "whatsapp"],
    "fonte_verificacao": "STJ — HC 598.051/SP",
    "verificacao_pendente": False,
    "similaridade": 0.91,  # coluna extra da consulta vetorial — deve ser ignorada
}


# --- utilitários ---------------------------------------------------------------

def test_vetor_para_sql_formata_literal_pgvector():
    assert _vetor_para_sql([0.1, -0.25, 2.0]) == "[0.1,-0.25,2.0]"


def test_tokens_de_busca_filtra_curto_e_normaliza():
    assert _tokens_de_busca("HC de má fé em WhatsApp") == ["whatsapp"]
    assert _tokens_de_busca("Cadeia DE custódia") == ["cadeia", "custódia"]
    assert _tokens_de_busca("  ") == []


def test_fake_embedder_satisfaz_o_contrato():
    assert isinstance(FakeEmbedder(), EmbedderPort)


# --- FonteSupabase: consulta vetorial --------------------------------------------

def test_busca_vetorial_usa_cosseno_limiar_e_limite():
    db, emb = FakeDB(linhas=[LINHA]), FakeEmbedder()
    fonte = FonteSupabase(db, emb)
    achados = executar(fonte.buscar_por_semelhanca("espelhamento de whatsapp", limite=3))
    assert [p.numero for p in achados] == ["HC 598.051/SP"]
    assert emb.chamadas == [["espelhamento de whatsapp"]]
    query, args = db.consultas[0]
    assert "vetor_semantico <=> $1::vector" in query
    assert "ORDER BY vetor_semantico <=> $1::vector" in query
    assert "vetor_semantico IS NOT NULL" in query
    assert "NOT verificacao_pendente" in query          # citabilidade no SQL
    assert args[0].startswith("[0.1,0.1,")               # literal pgvector
    assert args[1] == 0.7 and args[2] == 3               # limiar e limite


def test_limiar_customizado_e_repassado():
    db = FakeDB(linhas=[])
    fonte = FonteSupabase(db, FakeEmbedder(), limiar_similaridade=0.85)
    executar(fonte.buscar_por_semelhanca("x" * 5))
    assert db.consultas[0][1][1] == 0.85


def test_query_vazia_nao_consulta_nada():
    db = FakeDB()
    fonte = FonteSupabase(db, FakeEmbedder())
    assert executar(fonte.buscar_por_semelhanca("   ")) == []
    assert db.consultas == []


# --- FonteSupabase: contingências (fallback honesto) ------------------------------

def test_sem_embedder_cai_no_fallback_por_tags():
    db = FakeDB(linhas=[LINHA])
    fonte = FonteSupabase(db, embedder=None)
    achados = executar(fonte.buscar_por_semelhanca("nulidade por whatsapp", limite=1))
    assert len(achados) == 1
    query, args = db.consultas[0]
    assert "tags && $1::text[]" in query                 # rota de tags
    assert "vetor_semantico" not in query
    assert args[0] == ["nulidade", "por", "whatsapp"]


def test_falha_do_embedder_cai_no_fallback_sem_excecao():
    db = FakeDB(linhas=[LINHA])
    fonte = FonteSupabase(db, FakeEmbedder(erro=TimeoutError("provedor fora")))
    achados = executar(fonte.buscar_por_semelhanca("nulidade"))
    assert len(achados) == 1
    assert "tags &&" in db.consultas[0][0]


def test_falha_do_banco_na_rota_vetorial_cai_no_fallback():
    db = FakeDB(linhas=[LINHA], erro=RuntimeError("extensão vector ausente"))
    fonte = FonteSupabase(db, FakeEmbedder())
    achados = executar(fonte.buscar_por_semelhanca("nulidade"))
    assert len(achados) == 1
    # 1ª consulta: vetorial (falhou); 2ª: fallback por tags.
    assert "vetor_semantico" in db.consultas[0][0]
    assert "tags &&" in db.consultas[1][0]


# --- FonteJsonVerificada: ranking local-first --------------------------------------

@pytest.fixture
def fonte_json(tmp_path):
    base = {
        "tema": "cadeia de custódia",
        "precedentes": [
            {
                "numero": "HC 598.051/SP",
                "tese": "quebra da cadeia de custódia em espelhamento de WhatsApp",
                "tags": ["nulidade", "whatsapp"],
                "fonte_verificacao": "STJ",
            },
            {
                "numero": "Súmula 444/STJ",
                "tese": "veda inquéritos em curso para agravar a pena-base",
                "tags": ["dosimetria"],
                "fonte_verificacao": "STJ",
            },
        ],
    }
    (tmp_path / "03.json").write_text(json.dumps(base, ensure_ascii=False), "utf-8")
    return FonteJsonVerificada(tmp_path)


def test_json_ranqueia_por_sobreposicao_de_tokens(fonte_json):
    achados = executar(
        fonte_json.buscar_por_semelhanca("quebra de custódia no whatsapp")
    )
    assert [p.numero for p in achados] == ["HC 598.051/SP"]


def test_json_respeita_o_limite(fonte_json):
    achados = executar(fonte_json.buscar_por_semelhanca("pena-base whatsapp", limite=1))
    assert len(achados) == 1


def test_json_query_sem_tokens_uteis_devolve_vazio(fonte_json):
    assert executar(fonte_json.buscar_por_semelhanca("a de o")) == []


# --- contrato ---------------------------------------------------------------------

def test_ambas_as_fontes_seguem_satisfazendo_o_contrato(fonte_json):
    assert isinstance(fonte_json, FonteDePrecedentes)
    assert isinstance(FonteSupabase(FakeDB()), FonteDePrecedentes)
