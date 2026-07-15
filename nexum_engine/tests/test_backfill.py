"""Backfill de embeddings: idempotência, lotes, dry-run e falha-alto."""

import asyncio

import pytest

from nexum_engine.verdade.backfill_embeddings import (
    RelatorioBackfill,
    backfill_embeddings,
)


def executar(coro):
    return asyncio.run(coro)


class FakeEmbedder:
    def __init__(self, dim=4, erro=None, devolver_a_menos=False):
        self.dim = dim
        self.erro = erro
        self.devolver_a_menos = devolver_a_menos
        self.lotes: list[list[str]] = []

    async def embed(self, textos):
        if self.erro:
            raise self.erro
        self.lotes.append(list(textos))
        n = len(textos) - (1 if self.devolver_a_menos else 0)
        return [[0.5] * self.dim for _ in range(n)]


class FakeDB:
    """DatabasePort falso de ESCRITA permitida (papel service role)."""

    def __init__(self, linhas=()):
        self.linhas = list(linhas)
        self.selects = []
        self.updates = []

    async def fetch(self, query, *args):
        self.selects.append(query)
        return self.linhas

    async def fetchrow(self, query, *args):
        raise AssertionError("não usado")

    async def execute(self, query, *args):
        self.updates.append((query, args))
        return "UPDATE 1"


def _linha(n, tese="tese", ementa="ementa"):
    return {"numero_normalizado": n, "tese": tese, "ementa": ementa}


def test_seleciona_apenas_citaveis_sem_vetor():
    db = FakeDB()
    executar(backfill_embeddings(db, FakeEmbedder()))
    q = db.selects[0]
    assert "vetor_semantico IS NULL" in q
    assert "NOT verificacao_pendente" in q and "fonte_verificacao <> ''" in q


def test_atualiza_com_literal_pgvector_e_now():
    db = FakeDB(linhas=[_linha("HC 1/SP"), _linha("HC 2/SP")])
    rel = executar(backfill_embeddings(db, FakeEmbedder()))
    assert rel.candidatos == 2 and rel.atualizados == 2 and not rel.dry_run
    query, args = db.updates[0]
    assert "SET vetor_semantico = $1::vector" in query
    assert "atualizado_em = now()" in query
    assert args == ("[0.5,0.5,0.5,0.5]", "HC 1/SP")


def test_lotes_respeitam_o_tamanho():
    db = FakeDB(linhas=[_linha(f"HC {i}/SP") for i in range(5)])
    emb = FakeEmbedder()
    executar(backfill_embeddings(db, emb, lote=2))
    assert [len(l) for l in emb.lotes] == [2, 2, 1]


def test_dry_run_conta_sem_chamar_provedor_nem_gravar():
    db = FakeDB(linhas=[_linha("HC 1/SP")])
    emb = FakeEmbedder()
    rel = executar(backfill_embeddings(db, emb, dry_run=True))
    assert rel == RelatorioBackfill(candidatos=1, atualizados=0, dry_run=True)
    assert emb.lotes == [] and db.updates == []
    assert "ensaio" in str(rel)


def test_base_completa_e_noop():
    rel = executar(backfill_embeddings(FakeDB(), FakeEmbedder()))
    assert rel.candidatos == 0 and rel.atualizados == 0


def test_texto_vazio_falha_alto_com_o_numero():
    db = FakeDB(linhas=[_linha("HC 1/SP", tese="", ementa="")])
    with pytest.raises(RuntimeError, match="HC 1/SP"):
        executar(backfill_embeddings(db, FakeEmbedder()))
    assert db.updates == []


def test_contagem_divergente_do_provedor_aborta_sem_gravar():
    db = FakeDB(linhas=[_linha("HC 1/SP"), _linha("HC 2/SP")])
    with pytest.raises(RuntimeError, match="abortando"):
        executar(backfill_embeddings(db, FakeEmbedder(devolver_a_menos=True)))
    assert db.updates == []


def test_falha_do_provedor_propaga_sem_mascarar():
    db = FakeDB(linhas=[_linha("HC 1/SP")])
    with pytest.raises(TimeoutError):
        executar(backfill_embeddings(db, FakeEmbedder(erro=TimeoutError())))


def test_lote_invalido():
    with pytest.raises(ValueError):
        executar(backfill_embeddings(FakeDB(), FakeEmbedder(), lote=0))
