"""Medição de latência da busca vetorial — p50/p95/p99 (operador).

Utilitário de OPERADOR (somente leitura), não da engine em runtime: mede a
latência fim-a-fim da consulta vetorial de PRODUÇÃO (o mesmo SQL de
``FonteSupabase.buscar_por_semelhanca``, incluindo limiar e filtros) sob
concorrência controlada, e reporta p50/p95/p99, média, mínimo e máximo.

Método:

- As consultas são os próprios vetores da base (self-queries, como em
  ``validar_recall``): zero credenciais além do pool injetado — nenhum
  provedor de embeddings é chamado.
- ``concorrencia`` limita quantas consultas voam em paralelo (semáforo);
  ``repeticoes`` repete cada vetor amostrado; ``aquecimento`` executa
  N consultas sequenciais ANTES da medição e as descarta (caches frios,
  conexões do pool, JIT do planner).
- Percentis por nearest-rank sobre as latências ordenadas — sem
  interpolação, cada percentil é uma medição que de fato aconteceu.

Leituras honestas exigem contexto honesto:

- A latência inclui a REDE até o banco: rode de onde a engine roda em
  produção, ou os números não valem para ela.
- p95/p99 estáveis pedem volume: mire ao menos ~200 medições
  (``amostra`` × ``repeticoes``).
- Qualquer falha de consulta ABORTA a medição (erro propaga cru):
  estatística com buraco é pior que nenhuma.

Uso (gatilho HITL):

    from nexum_engine.adapters import AsyncpgAdapter
    from nexum_engine.verdade.medir_latencia import medir_latencia

    rel = await medir_latencia(
        AsyncpgAdapter(pool), k=5, concorrencia=8, repeticoes=5,
        aquecimento=8,
    )
    print(rel)
"""

from __future__ import annotations

import asyncio
import math
import time
from dataclasses import dataclass
from typing import Callable

from ..ports import DatabasePort
from .fontes import LIMIAR_SIMILARIDADE_PADRAO, FonteSupabase, _vetor_para_sql
from .validar_recall import _vetor_de_sql

_CITAVEL = FonteSupabase._CITAVEL
_COLUNAS = FonteSupabase._COLUNAS


@dataclass(frozen=True)
class RelatorioLatencia:
    k: int
    concorrencia: int
    medicoes: int        # consultas medidas (sem contar aquecimento)
    p50_ms: float
    p95_ms: float
    p99_ms: float
    media_ms: float
    minimo_ms: float
    maximo_ms: float

    def __str__(self) -> str:  # legível no terminal do operador
        return (
            f"latência k={self.k} (c={self.concorrencia}, "
            f"n={self.medicoes}): p50 {self.p50_ms:.1f} ms · "
            f"p95 {self.p95_ms:.1f} ms · p99 {self.p99_ms:.1f} ms "
            f"(média {self.media_ms:.1f}, mín {self.minimo_ms:.1f}, "
            f"máx {self.maximo_ms:.1f})"
        )


def _percentil(ordenadas: list[float], p: float) -> float:
    """Nearest-rank: o valor reportado é uma medição real, não interpolada."""
    indice = max(1, math.ceil(len(ordenadas) * p / 100.0))
    return ordenadas[indice - 1]


def _montar_consulta(tribunal: str | None, tema: str | None) -> str:
    """O MESMO SQL de produção de ``buscar_por_semelhanca``, com a mesma
    numeração dinâmica de binds: $1 vetor, $2 limiar, filtros, LIMIT."""
    pos = 2
    filtros = ""
    if tribunal is not None:
        pos += 1
        filtros += f" AND upper(tribunal) = upper(${pos})"
    if tema is not None:
        pos += 1
        filtros += f" AND upper(tema) = upper(${pos})"
    return (
        f"SELECT {_COLUNAS}, "
        f"1 - (vetor_semantico <=> $1::vector) AS similaridade "
        f"FROM precedentes_verificados "
        f"WHERE {_CITAVEL} AND vetor_semantico IS NOT NULL "
        f"AND 1 - (vetor_semantico <=> $1::vector) >= $2"
        f"{filtros} "
        f"ORDER BY vetor_semantico <=> $1::vector "
        f"LIMIT ${pos + 1}"
    )


async def medir_latencia(
    db: DatabasePort,
    *,
    k: int = 5,
    concorrencia: int = 8,
    repeticoes: int = 1,
    amostra: int | None = None,
    aquecimento: int = 0,
    tribunal: str | None = None,
    tema: str | None = None,
    limiar: float = LIMIAR_SIMILARIDADE_PADRAO,
    relogio: Callable[[], float] | None = None,
) -> RelatorioLatencia:
    """Mede a latência da consulta vetorial de produção sob concorrência.

    ``amostra`` limita quantos vetores distintos servem de consulta (os
    primeiros N em ordem de ``numero_normalizado`` — determinístico);
    ``None`` usa todos. ``relogio`` existe para injeção nos testes; o
    padrão é ``time.perf_counter``.
    """
    if k < 1:
        raise ValueError("k deve ser >= 1")
    if concorrencia < 1:
        raise ValueError("concorrencia deve ser >= 1")
    if repeticoes < 1:
        raise ValueError("repeticoes deve ser >= 1")
    if aquecimento < 0:
        raise ValueError("aquecimento deve ser >= 0")
    if amostra is not None and amostra < 1:
        raise ValueError("amostra deve ser >= 1 (ou None para todas)")

    agora = relogio or time.perf_counter
    linhas = await db.fetch(
        "SELECT numero_normalizado, vetor_semantico "
        "FROM precedentes_verificados "
        f"WHERE {_CITAVEL} AND vetor_semantico IS NOT NULL "
        "ORDER BY numero_normalizado"
    )
    if not linhas:
        raise RuntimeError(
            "nenhum precedente vetorizado — rode o backfill antes da medição"
        )
    base = [
        (
            l["numero_normalizado"],
            _vetor_de_sql(l["vetor_semantico"], l["numero_normalizado"]),
        )
        for l in linhas
    ]
    consultas = base if amostra is None else base[:amostra]
    sql = _montar_consulta(tribunal, tema)
    fixos: list = [limiar]
    if tribunal is not None:
        fixos.append(tribunal.strip())
    if tema is not None:
        fixos.append(tema.strip())
    fixos.append(k)

    async def _uma(literal: str) -> float:
        inicio = agora()
        await db.fetch(sql, literal, *fixos)
        return (agora() - inicio) * 1000.0

    # Aquecimento sequencial, fora da estatística.
    for i in range(aquecimento):
        await _uma(_vetor_para_sql(consultas[i % len(consultas)][1]))

    semaforo = asyncio.Semaphore(concorrencia)

    async def _tarefa(literal: str) -> float:
        async with semaforo:
            return await _uma(literal)

    latencias = list(
        await asyncio.gather(*[
            _tarefa(_vetor_para_sql(vetor))
            for _, vetor in consultas
            for _ in range(repeticoes)
        ])
    )
    ordenadas = sorted(latencias)
    return RelatorioLatencia(
        k=k,
        concorrencia=concorrencia,
        medicoes=len(ordenadas),
        p50_ms=_percentil(ordenadas, 50),
        p95_ms=_percentil(ordenadas, 95),
        p99_ms=_percentil(ordenadas, 99),
        media_ms=sum(ordenadas) / len(ordenadas),
        minimo_ms=ordenadas[0],
        maximo_ms=ordenadas[-1],
    )
