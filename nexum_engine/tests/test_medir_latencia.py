"""Latência p50/p95/p99 da consulta vetorial: relógio injetado, sem rede."""

import asyncio
import math

import pytest

from nexum_engine.verdade.medir_latencia import (
    RelatorioLatencia,
    _percentil,
    medir_latencia,
)


def executar(coro):
    return asyncio.run(coro)


def _vetores(n=4):
    return {
        f"HC {i}/SP": [math.cos(i * 0.7), math.sin(i * 0.7)] for i in range(n)
    }


class RelogioFalso:
    """Relógio determinístico: avança só quando o FakeDB 'executa'."""

    def __init__(self):
        self.agora = 0.0

    def __call__(self) -> float:
        return self.agora


class FakeDB:
    """DatabasePort falso: devolve os vetores no SELECT de base e consome
    uma duração roteirizada (em ms) a cada consulta vetorial medida."""

    def __init__(self, vetores, duracoes_ms, relogio, erro=None):
        self.vetores = dict(vetores)
        self.duracoes_ms = list(duracoes_ms)
        self.relogio = relogio
        self.erro = erro
        self.consultas_vetoriais = []
        self.em_voo = 0
        self.max_em_voo = 0

    async def fetch(self, query, *args):
        if "<=>" not in query:
            return [
                {"numero_normalizado": n, "vetor_semantico": list(v)}
                for n, v in sorted(self.vetores.items())
            ]
        if self.erro:
            raise self.erro
        self.em_voo += 1
        self.max_em_voo = max(self.max_em_voo, self.em_voo)
        await asyncio.sleep(0.001)  # força sobreposição real das tarefas
        self.consultas_vetoriais.append((query, args))
        self.relogio.agora += self.duracoes_ms[
            (len(self.consultas_vetoriais) - 1) % len(self.duracoes_ms)
        ] / 1000.0
        self.em_voo -= 1
        return []

    async def fetchrow(self, query, *args):
        raise AssertionError("não usado")

    async def execute(self, query, *args):
        raise AssertionError("utilitário é somente leitura")


def test_percentil_nearest_rank_e_medicao_real():
    ordenadas = [float(x) for x in range(10, 110, 10)]  # 10..100
    assert _percentil(ordenadas, 50) == 50.0
    assert _percentil(ordenadas, 95) == 100.0
    assert _percentil(ordenadas, 99) == 100.0
    assert _percentil([42.0], 50) == 42.0


def test_relatorio_com_duracoes_roteirizadas():
    relogio = RelogioFalso()
    db = FakeDB(_vetores(4), duracoes_ms=range(10, 50, 10), relogio=relogio)
    rel = executar(medir_latencia(db, k=5, concorrencia=1, relogio=relogio))
    assert rel.medicoes == 4 and rel.concorrencia == 1
    assert rel.minimo_ms == pytest.approx(10.0)
    assert rel.maximo_ms == pytest.approx(40.0)
    assert rel.p50_ms == pytest.approx(20.0)
    assert rel.media_ms == pytest.approx(25.0)
    assert "p95" in str(rel) and "k=5" in str(rel)


def test_sql_medido_e_o_de_producao_com_e_sem_filtros():
    relogio = RelogioFalso()
    db = FakeDB(_vetores(2), [5], relogio)
    executar(medir_latencia(db, k=3, concorrencia=1, relogio=relogio))
    query, args = db.consultas_vetoriais[0]
    assert "AS similaridade" in query
    assert ">= $2" in query and "LIMIT $3" in query
    assert "upper(" not in query
    assert args[1] == 0.7 and args[2] == 3  # limiar de produção e k

    db2 = FakeDB(_vetores(2), [5], relogio)
    executar(medir_latencia(
        db2, k=3, concorrencia=1, relogio=relogio,
        tribunal="STJ", tema="júri",
    ))
    query2, args2 = db2.consultas_vetoriais[0]
    assert "AND upper(tribunal) = upper($3)" in query2
    assert "AND upper(tema) = upper($4)" in query2
    assert "LIMIT $5" in query2
    assert args2[2:] == ("STJ", "júri", 3)


def test_concorrencia_limita_e_de_fato_paraleliza():
    relogio = RelogioFalso()
    db = FakeDB(_vetores(4), [5], relogio)
    executar(medir_latencia(
        db, concorrencia=3, repeticoes=6, relogio=relogio
    ))
    assert len(db.consultas_vetoriais) == 24
    assert db.max_em_voo <= 3
    assert db.max_em_voo >= 2  # houve paralelismo real


def test_aquecimento_fica_fora_da_estatistica():
    relogio = RelogioFalso()
    db = FakeDB(
        _vetores(3), duracoes_ms=[1000, 1000, 10, 20, 30], relogio=relogio
    )
    rel = executar(medir_latencia(
        db, concorrencia=1, aquecimento=2, relogio=relogio
    ))
    assert rel.medicoes == 3
    assert rel.maximo_ms == pytest.approx(30.0)  # os 1000 ms foram descartados


def test_amostra_e_repeticoes_definem_o_volume():
    relogio = RelogioFalso()
    db = FakeDB(_vetores(5), [5], relogio)
    rel = executar(medir_latencia(
        db, concorrencia=2, amostra=2, repeticoes=4, relogio=relogio
    ))
    assert rel.medicoes == 8 and len(db.consultas_vetoriais) == 8


def test_base_sem_vetores_falha_alto():
    relogio = RelogioFalso()
    with pytest.raises(RuntimeError, match="backfill"):
        executar(medir_latencia(FakeDB({}, [5], relogio), relogio=relogio))


def test_falha_de_consulta_aborta_sem_mascarar():
    relogio = RelogioFalso()
    db = FakeDB(_vetores(2), [5], relogio, erro=TimeoutError("banco fora"))
    with pytest.raises(TimeoutError):
        executar(medir_latencia(db, relogio=relogio))


def test_parametros_invalidos():
    relogio = RelogioFalso()
    db = FakeDB(_vetores(2), [5], relogio)
    for chamada in (
        medir_latencia(db, k=0, relogio=relogio),
        medir_latencia(db, concorrencia=0, relogio=relogio),
        medir_latencia(db, repeticoes=0, relogio=relogio),
        medir_latencia(db, aquecimento=-1, relogio=relogio),
        medir_latencia(db, amostra=0, relogio=relogio),
    ):
        with pytest.raises(ValueError):
            executar(chamada)
