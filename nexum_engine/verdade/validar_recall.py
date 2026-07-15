"""Validação de Recall@K — índice HNSW de produção vs. gabarito exato.

Utilitário de OPERADOR (somente leitura), não da engine em runtime: mede a
qualidade do índice ``idx_precedentes_vetor`` comparando, para cada
precedente vetorizado (self-query, leave-one-out), o top-K devolvido pelo
caminho de produção — o MESMO SQL de ``FonteSupabase.buscar_por_semelhanca``,
que o planner atende pelo HNSW — contra o ranking exato recalculado em
Python sobre os mesmos vetores.

Decisões que importam aqui:

- O gabarito exato é local (distância de cosseno em Python), e não um
  ``SET LOCAL enable_indexscan = off``: o ``DatabasePort`` roda cada
  consulta em conexão possivelmente distinta do pool, então GUC de
  sessão/transação não tem garantia nenhuma. O cálculo local é
  determinístico e não exige nada além de SELECT.
- O limiar de similaridade de produção fica DE FORA das duas pontas:
  recall mede o índice, não a regra de negócio — um limiar cortaria
  vizinhos das duas listas de formas diferentes e mascararia o resultado.
- Rodar com o papel de LEITURA da engine é o cenário fiel: a RLS já
  restringe às linhas citáveis — exatamente o universo que a busca de
  produção enxerga.
- Empates de distância são desempatados por ``numero_normalizado`` no
  gabarito; empates reais no banco podem custar frações de recall — com
  embeddings reais isso é raro, e um recall < 1.0 persistente indica
  índice degradado (rebuild, ou ``hnsw.ef_search`` maior no servidor).

Uso (gatilho HITL):

    from nexum_engine.adapters import AsyncpgAdapter
    from nexum_engine.verdade.validar_recall import validar_recall

    rel = await validar_recall(AsyncpgAdapter(pool), k=5)
    print(rel)  # recall@5: média 0.987, mínimo 0.800 (pior: ...) — ...
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence

from ..ports import DatabasePort
from .fontes import FonteSupabase, _vetor_para_sql

# Única fonte do predicado de citabilidade — o mesmo da busca de produção.
_CITAVEL = FonteSupabase._CITAVEL


@dataclass(frozen=True)
class RelatorioRecall:
    k: int
    consultas: int      # amostras efetivamente medidas
    vetorizados: int    # universo citável com vetor no banco
    recall_medio: float
    recall_minimo: float
    pior_consulta: str  # numero_normalizado do pior caso

    def __str__(self) -> str:  # legível no terminal do operador
        return (
            f"recall@{self.k}: média {self.recall_medio:.3f}, "
            f"mínimo {self.recall_minimo:.3f} (pior: {self.pior_consulta}) — "
            f"{self.consultas} consulta(s) sobre "
            f"{self.vetorizados} vetorizado(s)"
        )


def _vetor_de_sql(valor: Any, numero: str) -> list[float]:
    """Vetor vindo do banco: lista (codec pgvector) ou literal ``'[...]'``."""
    if isinstance(valor, str):
        corpo = valor.strip()
        if not (corpo.startswith("[") and corpo.endswith("]")):
            raise RuntimeError(
                f"vetor_semantico ilegível em {numero!r}: {valor!r}"
            )
        return [float(x) for x in corpo[1:-1].split(",") if x.strip()]
    return [float(x) for x in valor]


def _distancia_cosseno(a: Sequence[float], b: Sequence[float]) -> float:
    """Mesma métrica do índice (``vector_cosine_ops``): 1 − cos(a, b)."""
    prod = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return 1.0 - prod / (na * nb)


async def validar_recall(
    db: DatabasePort, *, k: int = 5, amostra: int | None = None
) -> RelatorioRecall:
    """Mede o Recall@K do índice vetorial contra o gabarito exato.

    ``amostra`` limita quantos precedentes servem de consulta (os primeiros
    N em ordem de ``numero_normalizado`` — determinístico e reproduzível);
    ``None`` usa todos. Exige ao menos ``k + 1`` vetorizados: com menos que
    isso o top-K não é mensurável. FALHA ALTO em dados inconsistentes
    (vetor ilegível, dimensão divergente, norma zero) — isso é erro de
    operação/backfill, nunca algo a mascarar.
    """
    if k < 1:
        raise ValueError("k deve ser >= 1")
    if amostra is not None and amostra < 1:
        raise ValueError("amostra deve ser >= 1 (ou None para todas)")

    linhas = await db.fetch(
        "SELECT numero_normalizado, vetor_semantico "
        "FROM precedentes_verificados "
        f"WHERE {_CITAVEL} AND vetor_semantico IS NOT NULL "
        "ORDER BY numero_normalizado"
    )
    if len(linhas) < k + 1:
        raise RuntimeError(
            f"apenas {len(linhas)} precedente(s) vetorizado(s) — Recall@{k} "
            f"exige ao menos {k + 1}; rode o backfill antes da validação"
        )

    base = [
        (
            l["numero_normalizado"],
            _vetor_de_sql(l["vetor_semantico"], l["numero_normalizado"]),
        )
        for l in linhas
    ]
    dim = len(base[0][1])
    problemas = [
        n for n, v in base
        if len(v) != dim or math.sqrt(sum(x * x for x in v)) == 0.0
    ]
    if problemas:
        raise RuntimeError(
            "vetor(es) inválido(s) (dimensão divergente ou norma zero) — "
            f"refazer o backfill de: {problemas}"
        )

    consultas = base if amostra is None else base[:amostra]
    soma = 0.0
    minimo, pior = 2.0, ""  # recall ∈ [0, 1]; sentinela acima do teto
    for numero, vetor in consultas:
        exato = sorted(
            (_distancia_cosseno(vetor, v), n) for n, v in base if n != numero
        )[:k]
        gabarito = {n for _, n in exato}
        devolvidas = await db.fetch(
            "SELECT numero_normalizado FROM precedentes_verificados "
            f"WHERE {_CITAVEL} AND vetor_semantico IS NOT NULL "
            "AND numero_normalizado <> $2 "
            "ORDER BY vetor_semantico <=> $1::vector LIMIT $3",
            _vetor_para_sql(vetor),
            numero,
            k,
        )
        if len(devolvidas) > k:
            raise RuntimeError(
                f"banco devolveu {len(devolvidas)} linhas para LIMIT {k} — "
                "adaptador/consulta violando o contrato"
            )
        obtidos = {l["numero_normalizado"] for l in devolvidas}
        recall = len(gabarito & obtidos) / k
        soma += recall
        if recall < minimo:
            minimo, pior = recall, numero

    return RelatorioRecall(
        k=k,
        consultas=len(consultas),
        vetorizados=len(base),
        recall_medio=soma / len(consultas),
        recall_minimo=minimo,
        pior_consulta=pior,
    )
