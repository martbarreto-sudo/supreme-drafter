"""Testes unitarios da camada engine (pgvector) — deterministicos, sem DB/rede.

Cobrem a REGRA CENTRAL (L2-normalize na escrita + cosseno == 1 - dot), o
chunking com sobreposicao/fls, o fake deterministico e o construtor de query KNN
(`<=>`) contra cursores fake. Um teste de ranking em Python puro prova a escolha
da metrica independentemente do banco.
"""

from __future__ import annotations

import importlib
import math

import pytest

from nexum.engine import chunking, embeddings, retrieval, vectors
from nexum.engine.chunking import chunk_text
from nexum.engine.embeddings import DeterministicFakeEmbedder
from nexum.engine.vectors import (
    EMBEDDING_DIM,
    cosine_distance,
    cosine_similarity,
    l2_normalize,
    to_pgvector_literal,
)


# --------------------------------------------------------------------------- #
# Fakes (mesmo estilo de nexum/tests/test_pipeline.py)
# --------------------------------------------------------------------------- #
class FakeCursor:
    def __init__(self, rows: list[tuple]) -> None:
        self._rows = rows
        self.executed: list[tuple] = []

    def execute(self, sql: str, params: tuple = ()) -> None:
        self.executed.append((sql, params))

    def fetchall(self) -> list[tuple]:
        return self._rows

    def close(self) -> None:
        pass


class FakeConn:
    def __init__(self, rows: list[tuple] | None = None) -> None:
        self._cursor = FakeCursor(rows or [])
        self.committed = False
        self.rolled_back = False

    def cursor(self) -> FakeCursor:
        return self._cursor

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def _norm(vec) -> float:
    return math.sqrt(sum(x * x for x in vec))


def _parse_literal(literal: str) -> list[float]:
    assert literal.startswith("[") and literal.endswith("]")
    return [float(x) for x in literal[1:-1].split(",")]


# --------------------------------------------------------------------------- #
# vectors: L2-normalize + identidade do cosseno
# --------------------------------------------------------------------------- #
def test_l2_normalize_unit_norm() -> None:
    vec = [float(i + 1) for i in range(EMBEDDING_DIM)]
    unit = l2_normalize(vec)
    assert len(unit) == EMBEDDING_DIM
    assert _norm(unit) == pytest.approx(1.0, abs=1e-12)


def test_l2_normalize_raises_on_wrong_dim() -> None:
    with pytest.raises(ValueError):
        l2_normalize([1.0, 2.0, 3.0])  # dim != EMBEDDING_DIM


def test_l2_normalize_raises_on_zero_vector() -> None:
    with pytest.raises(ValueError):
        l2_normalize([0.0] * EMBEDDING_DIM)


def test_cosine_distance_equals_one_minus_dot_for_normalized() -> None:
    a = l2_normalize([float((i * 7) % 13 + 1) for i in range(EMBEDDING_DIM)])
    b = l2_normalize([float((i * 3) % 11 + 1) for i in range(EMBEDDING_DIM)])
    dot = sum(x * y for x, y in zip(a, b))
    assert cosine_distance(a, b) == pytest.approx(1.0 - dot, abs=1e-9)
    assert cosine_similarity(a, b) == pytest.approx(dot, abs=1e-9)


def test_to_pgvector_literal_roundtrip() -> None:
    vec = l2_normalize([float(i + 1) for i in range(EMBEDDING_DIM)])
    parsed = _parse_literal(to_pgvector_literal(vec))
    assert parsed == pytest.approx(vec, abs=1e-12)


# --------------------------------------------------------------------------- #
# chunking
# --------------------------------------------------------------------------- #
LEGAL_TEXT = (
    "Trata-se de peticao inicial. O reu foi denunciado pela suposta pratica "
    "do delito. A defesa sustenta a nulidade da prova, conforme fls. 42 dos "
    "autos, por ausencia de cadeia de custodia.\n\n"
    "No merito, argumenta-se que a materialidade nao restou comprovada. "
    "Os laudos periciais sao contraditorios entre si. A testemunha ocular "
    "apresentou versao inconsistente em juizo.\n\n"
    "Requer-se, ao final, a absolvicao com fundamento no artigo 386 do CPP. "
    "Subsidiariamente, pleiteia-se a desclassificacao da conduta. "
    "Protesta-se por todos os meios de prova admitidos em direito."
)


def test_chunk_text_multiple_ordered_chunks_with_overlap() -> None:
    chunks = chunk_text(LEGAL_TEXT, target_tokens=30, overlap_ratio=0.3)
    assert len(chunks) > 1
    # chunk_index monotonico crescente comecando em 0.
    assert [c.index for c in chunks] == list(range(len(chunks)))
    # Sobreposicao: algum token do fim do chunk i reaparece no inicio do i+1.
    for i in range(len(chunks) - 1):
        tail = set(chunks[i].content.split()[-4:])
        head = set(chunks[i + 1].content.split())
        assert tail & head, f"sem overlap entre chunk {i} e {i + 1}"


def test_chunk_text_extracts_fls_ref() -> None:
    chunks = chunk_text(LEGAL_TEXT, target_tokens=30, overlap_ratio=0.1)
    refs = [c.fls_ref for c in chunks if c.fls_ref]
    assert "fls. 42" in refs


def test_chunk_text_empty_returns_empty() -> None:
    assert chunk_text("   \n\n  ") == []


def test_chunk_token_count_is_whitespace_proxy() -> None:
    chunks = chunk_text("um dois tres quatro cinco", target_tokens=100)
    assert len(chunks) == 1
    assert chunks[0].token_count == 5


# --------------------------------------------------------------------------- #
# DeterministicFakeEmbedder
# --------------------------------------------------------------------------- #
def test_fake_embedder_deterministic_and_unit_norm() -> None:
    emb = DeterministicFakeEmbedder()
    v1 = emb.embed(["habeas corpus"])[0]
    v2 = emb.embed(["habeas corpus"])[0]
    v3 = emb.embed(["recurso especial"])[0]

    assert len(v1) == EMBEDDING_DIM
    assert v1 == v2  # mesmo texto -> vetor identico
    assert v1 != v3  # texto diferente -> vetor diferente
    assert _norm(v1) == pytest.approx(1.0, abs=1e-9)
    assert _norm(v3) == pytest.approx(1.0, abs=1e-9)


def test_fake_embedder_respects_dim_param() -> None:
    emb = DeterministicFakeEmbedder(dim=32)
    vecs = emb.embed(["a", "b"])
    assert all(len(v) == 32 for v in vecs)
    assert _norm(vecs[0]) == pytest.approx(1.0, abs=1e-9)


def test_embedding_dim_respects_env_override(monkeypatch) -> None:
    """NEXUM_EMBEDDING_DIM redefine EMBEDDING_DIM apos reload do modulo.

    Restaura o estado global no finally (reload sem a env) para nao vazar para
    os demais testes — a suite deve ser deterministica ao rodar duas vezes.
    """

    monkeypatch.setenv("NEXUM_EMBEDDING_DIM", "16")
    try:
        importlib.reload(vectors)
        assert vectors.EMBEDDING_DIM == 16
        # l2_normalize passa a exigir 16 posicoes.
        unit = vectors.l2_normalize([1.0] * 16)
        assert len(unit) == 16
    finally:
        monkeypatch.delenv("NEXUM_EMBEDDING_DIM", raising=False)
        importlib.reload(vectors)
        importlib.reload(embeddings)
        importlib.reload(retrieval)
        assert vectors.EMBEDDING_DIM == 768


# --------------------------------------------------------------------------- #
# retrieval.search contra cursor fake
# --------------------------------------------------------------------------- #
def test_search_builds_cosine_knn_query() -> None:
    rows = [
        ("chunk-1", "src-1", "conteudo A", "fls. 42", 0.98),
        ("chunk-2", "src-1", "conteudo B", None, 0.71),
    ]
    conn = FakeConn(rows)
    query = [float(i % 5 + 1) for i in range(EMBEDDING_DIM)]

    results = retrieval.search(
        conn, workspace_id="ws-1", query_embedding=query, k=5
    )

    # Mapeamento para dicts.
    assert results[0] == {
        "chunk_id": "chunk-1",
        "source_id": "src-1",
        "content": "conteudo A",
        "fls_ref": "fls. 42",
        "similarity": 0.98,
    }
    assert results[1]["chunk_id"] == "chunk-2"

    sql, params = conn.cursor().executed[0]
    # Ordena pela distancia de cosseno `<=>`.
    assert "ORDER BY embedding <=> %s::vector" in sql
    assert "1 - (embedding <=> %s::vector)" in sql
    # Vincula: literal (SELECT), workspace_id, literal (ORDER BY), k.
    literal_1, workspace_id, literal_2, k = params
    assert workspace_id == "ws-1"
    assert k == 5
    assert literal_1 == literal_2  # mesmo vetor de consulta vinculado 2x
    # O literal vinculado esta L2-normalizado (norma ~ 1).
    assert _norm(_parse_literal(literal_1)) == pytest.approx(1.0, abs=1e-9)


def test_pure_python_ranking_nearest_first() -> None:
    """Prova, sem banco, que cosine_distance ranqueia o mais proximo primeiro."""

    emb = DeterministicFakeEmbedder()
    stored = {
        "sentenca condenatoria": emb.embed(["sentenca condenatoria"])[0],
        "peticao de habeas corpus": emb.embed(["peticao de habeas corpus"])[0],
        "laudo pericial balistico": emb.embed(["laudo pericial balistico"])[0],
    }
    query = emb.embed(["peticao de habeas corpus"])[0]

    ranked = sorted(
        stored.items(), key=lambda kv: cosine_distance(query, kv[1])
    )
    # O vetor identico ao query (mesma frase) fica em primeiro (distancia ~ 0).
    assert ranked[0][0] == "peticao de habeas corpus"
    assert cosine_distance(query, ranked[0][1]) == pytest.approx(0.0, abs=1e-9)


# --------------------------------------------------------------------------- #
# retrieval.upsert_chunks contra cursor fake
# --------------------------------------------------------------------------- #
def test_upsert_chunks_normalizes_and_has_on_conflict() -> None:
    chunks = chunk_text(LEGAL_TEXT, target_tokens=12, overlap_ratio=0.1)
    emb = DeterministicFakeEmbedder()
    vectors_out = emb.embed([c.content for c in chunks])
    conn = FakeConn()

    n = retrieval.upsert_chunks(conn, "src-1", "ws-1", chunks, vectors_out)

    assert n == len(chunks)
    assert conn.committed is True
    executed = conn.cursor().executed
    assert len(executed) == len(chunks)

    for sql, params in executed:
        assert "ON CONFLICT (source_id, chunk_index) DO UPDATE" in sql
        # embedding e o ultimo parametro; deve estar normalizado (norma ~ 1).
        embedding_literal = params[-1]
        assert _norm(_parse_literal(embedding_literal)) == pytest.approx(
            1.0, abs=1e-9
        )


def test_upsert_chunks_guards_length_mismatch() -> None:
    chunks = chunk_text(LEGAL_TEXT, target_tokens=20)
    conn = FakeConn()
    with pytest.raises(AssertionError):
        retrieval.upsert_chunks(conn, "src-1", "ws-1", chunks, [])
