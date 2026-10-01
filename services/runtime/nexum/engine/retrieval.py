"""Construtor e executor de consulta KNN por cosseno (pgvector `<=>`).

`search` faz a busca vizinho-mais-proximo filtrada por `workspace_id`, ordenando
pela distancia de cosseno (`<=>`) e retornando `similarity = 1 - distancia`.
`upsert_chunks` insere/atualiza chunks de forma idempotente
(`ON CONFLICT (source_id, chunk_index)`), aplicando a REGRA CENTRAL: cada
embedding e L2-normalizado ANTES de virar literal pgvector.

Opera sobre uma conexao DB-API (psycopg3) e e testavel com cursores fake — nao
importa driver algum no topo do modulo.
"""

from __future__ import annotations

from typing import Any, Sequence

from nexum.engine.vectors import l2_normalize, to_pgvector_literal

# KNN por cosseno. O MESMO literal do vetor de consulta (ja normalizado) e
# vinculado DUAS vezes: no SELECT (para calcular similarity) e no ORDER BY (para
# ordenar pela distancia `<=>`). O filtro por workspace_id garante isolamento de
# tenant e aproveita idx_chunks_workspace.
SEARCH_SQL = (
    "SELECT chunk_id, source_id, content, fls_ref, "
    "1 - (embedding <=> %s::vector) AS similarity "
    "FROM chunks "
    "WHERE workspace_id = %s "
    "ORDER BY embedding <=> %s::vector "
    "LIMIT %s"
)

# Upsert idempotente de um chunk. ON CONFLICT no par (source_id, chunk_index)
# atualiza o conteudo/embedding, permitindo reindexacao sem duplicar linhas.
UPSERT_CHUNK_SQL = (
    "INSERT INTO chunks "
    "(source_id, workspace_id, chunk_index, content, fls_ref, "
    "token_count, embedding) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s::vector) "
    "ON CONFLICT (source_id, chunk_index) DO UPDATE SET "
    "content = EXCLUDED.content, "
    "fls_ref = EXCLUDED.fls_ref, "
    "token_count = EXCLUDED.token_count, "
    "embedding = EXCLUDED.embedding"
)


def search(
    conn: Any,
    *,
    workspace_id: str,
    query_embedding: Sequence[float],
    k: int = 8,
) -> list[dict]:
    """Executa a busca KNN por cosseno e retorna linhas como dicts.

    L2-normaliza o embedding de consulta (REGRA CENTRAL: casa com os vetores
    normalizados na escrita, de modo que `<=>` == `1 - dot`), formata o literal
    pgvector e o vincula duas vezes (SELECT + ORDER BY), alem de `workspace_id`
    e `k`. Retorna ate `k` dicts com chaves
    `chunk_id, source_id, content, fls_ref, similarity`.
    """

    normalized = l2_normalize(query_embedding)
    literal = to_pgvector_literal(normalized)

    cur = conn.cursor()
    try:
        cur.execute(SEARCH_SQL, (literal, workspace_id, literal, k))
        rows = cur.fetchall()
    finally:
        close = getattr(cur, "close", None)
        if callable(close):
            close()

    return [
        {
            "chunk_id": row[0],
            "source_id": row[1],
            "content": row[2],
            "fls_ref": row[3],
            "similarity": row[4],
        }
        for row in rows
    ]


def upsert_chunks(
    conn: Any,
    source_id: str,
    workspace_id: str,
    chunks: Sequence[Any],
    embeddings: Sequence[Sequence[float]],
) -> int:
    """Insere/atualiza chunks com embeddings L2-normalizados (idempotente).

    `chunks` sao objetos com atributos `index`, `content`, `fls_ref`,
    `token_count` (ex.: `nexum.engine.chunking.Chunk`). Cada embedding e
    L2-normalizado ANTES de virar literal pgvector — esta e a regra de
    normalizacao na escrita. Retorna a quantidade de linhas processadas.

    Levanta `AssertionError` se `len(chunks) != len(embeddings)`.
    """

    assert len(chunks) == len(embeddings), (
        f"chunks ({len(chunks)}) e embeddings ({len(embeddings)}) "
        "devem ter o mesmo tamanho"
    )

    cur = conn.cursor()
    count = 0
    try:
        for chunk, embedding in zip(chunks, embeddings):
            literal = to_pgvector_literal(l2_normalize(embedding))
            cur.execute(
                UPSERT_CHUNK_SQL,
                (
                    source_id,
                    workspace_id,
                    chunk.index,
                    chunk.content,
                    chunk.fls_ref,
                    chunk.token_count,
                    literal,
                ),
            )
            count += 1
        conn.commit()
        return count
    except Exception:
        conn.rollback()
        raise
    finally:
        close = getattr(cur, "close", None)
        if callable(close):
            close()
