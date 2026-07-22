"""Regras de normalizacao vetorial do NEXUM (pgvector / busca semantica).

Este modulo concentra a REGRA CENTRAL da camada: vetores sao L2-normalizados na
ESCRITA. Com vetores unitarios, a distancia de cosseno vira `1 - produto_interno`
e casa exatamente com o operador `<=>` (`vector_cosine_ops`) do pgvector sob o
indice HNSW.

Implementacao em Python puro (apenas `math`), sem numpy: mantem o pacote leve e
os testes deterministicos sem dependencias nativas.
"""

from __future__ import annotations

import math
import os
from typing import Sequence


def _read_embedding_dim() -> int:
    """Le a dimensao do embedding da env `NEXUM_EMBEDDING_DIM` (default 768)."""

    raw = os.environ.get("NEXUM_EMBEDDING_DIM", "768")
    try:
        dim = int(raw)
    except (TypeError, ValueError):
        raise ValueError(
            f"NEXUM_EMBEDDING_DIM invalido: {raw!r} (esperado inteiro positivo)"
        )
    if dim <= 0:
        raise ValueError(
            f"NEXUM_EMBEDDING_DIM deve ser positivo, recebido {dim}"
        )
    return dim


# Dimensao default do embedding. Configuravel via env NEXUM_EMBEDDING_DIM.
# DEVE casar com o literal `vector(N)` em nexum/engine/schema.sql.
EMBEDDING_DIM: int = _read_embedding_dim()


def validate_dim(vec: Sequence[float], dim: int | None = None) -> None:
    """Valida que `vec` tem exatamente `dim` (default EMBEDDING_DIM) posicoes.

    Levanta `ValueError` quando o comprimento diverge da dimensao esperada.
    """

    expected = EMBEDDING_DIM if dim is None else dim
    if len(vec) != expected:
        raise ValueError(
            f"Dimensao invalida: esperado {expected}, recebido {len(vec)}"
        )


def l2_normalize(vec: Sequence[float], dim: int | None = None) -> list[float]:
    """Retorna o vetor unitario (norma L2 == 1) correspondente a `vec`.

    Valida a dimensao antes de normalizar. REGRA DO VETOR ZERO: um vetor de
    norma nula nao tem direcao definida e nao pode ser normalizado, portanto
    levanta `ValueError` em vez de dividir por zero ou devolver zeros (o que
    corromperia silenciosamente a busca por cosseno).
    """

    validate_dim(vec, dim)
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        raise ValueError(
            "Vetor de norma zero nao pode ser L2-normalizado "
            "(direcao indefinida)"
        )
    return [x / norm for x in vec]


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    """Produto interno de dois vetores de mesma dimensao."""

    if len(a) != len(b):
        raise ValueError(
            f"Vetores de dimensoes diferentes: {len(a)} vs {len(b)}"
        )
    return sum(x * y for x, y in zip(a, b))


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Similaridade de cosseno em [-1, 1] entre `a` e `b` (Python puro).

    Referencia para testes e para um fallback sem banco. Levanta `ValueError`
    se qualquer vetor tiver norma zero.
    """

    norm_a = math.sqrt(_dot(a, a))
    norm_b = math.sqrt(_dot(b, b))
    if norm_a == 0.0 or norm_b == 0.0:
        raise ValueError(
            "Similaridade de cosseno indefinida para vetor de norma zero"
        )
    return _dot(a, b) / (norm_a * norm_b)


def cosine_distance(a: Sequence[float], b: Sequence[float]) -> float:
    """Distancia de cosseno `1 - cosine_similarity(a, b)` (Python puro).

    Com vetores JA L2-normalizados vale a identidade `cosine_distance == 1 - dot`,
    exatamente o que o operador `<=>` do pgvector computa. Serve de referencia de
    ranking independente do banco.
    """

    return 1.0 - cosine_similarity(a, b)


def to_pgvector_literal(vec: Sequence[float]) -> str:
    """Formata `vec` como literal texto do pgvector: `'[0.1,0.2,...]'`.

    O psycopg3 adapta a string diretamente para o tipo `vector` via cast
    `%s::vector`. Em producao registrar-se-ia o adapter oficial do pacote
    `pgvector` (pgvector.psycopg.register_vector) para passar listas nativas;
    aqui optamos pelo literal texto por portabilidade e para evitar dependencia
    dura (o `pgvector` fica como extra OPCIONAL em requirements.txt).
    """

    return "[" + ",".join(repr(float(x)) for x in vec) + "]"
