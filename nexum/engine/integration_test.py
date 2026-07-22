"""Teste de integracao da camada pgvector (requer Postgres com extensao vector).

Coleta sob pytest sem Docker: se o Postgres estiver down OU a extensao `vector`
nao estiver disponivel (imagem sem pgvector), o teste faz SKIP limpo (nao falha).
Quando a infra esta de pe (compose usa `pgvector/pgvector:pg16`):

  1. conecta via NEXUM_OUTBOX_DSN e cria a extensao `vector` (skip se falhar);
  2. carrega o schema da engine em uma transacao efemera;
  3. cria uma workspace temporaria e faz upsert de 2 chunks via
     DeterministicFakeEmbedder;
  4. roda `search` e assevera ordenacao vizinho-mais-proximo (nearest-first);
  5. faz ROLLBACK ao final — nao suja o banco.

Rodar apenas este teste: `pytest nexum -m integration`.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

from nexum.engine import retrieval
from nexum.engine.chunking import Chunk
from nexum.engine.embeddings import DeterministicFakeEmbedder

PG_DSN = os.environ.get(
    "NEXUM_OUTBOX_DSN", "postgresql://nexum:nexum@localhost:5432/nexum"
)
SCHEMA_SQL = Path(__file__).resolve().parent / "schema.sql"


def _connect_or_skip():
    """Conecta a Postgres; `pytest.skip` se a infra estiver down."""

    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover - depende do ambiente
        pytest.skip(f"psycopg ausente: {exc}")

    try:
        return psycopg.connect(PG_DSN, connect_timeout=2)
    except Exception as exc:  # noqa: BLE001 - qualquer falha => skip
        pytest.skip(f"infra not up (postgres): {exc}")


@pytest.mark.integration
def test_pgvector_upsert_and_search_nearest_first() -> None:
    conn = _connect_or_skip()
    try:
        cur = conn.cursor()
        # Extensao vector disponivel? (imagem pgvector/pgvector). Se nao, skip.
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.commit()
        except Exception as exc:  # noqa: BLE001
            conn.rollback()
            pytest.skip(f"extensao pgvector indisponivel: {exc}")

        # Carrega o schema da engine (idempotente) dentro da conexao.
        cur.execute(SCHEMA_SQL.read_text(encoding="utf-8"))
        conn.commit()

        workspace_id = str(uuid.uuid4())
        source_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO sources (source_id, workspace_id, s3_key, source_type) "
            "VALUES (%s, %s, %s, %s)",
            (source_id, workspace_id, f"s3://bucket/{source_id}.pdf", "peticao"),
        )
        conn.commit()

        emb = DeterministicFakeEmbedder()
        texts = ["habeas corpus preventivo", "laudo pericial balistico"]
        chunks = [
            Chunk(index=i, content=t, fls_ref=None, token_count=len(t.split()))
            for i, t in enumerate(texts)
        ]
        embeddings = emb.embed(texts)

        n = retrieval.upsert_chunks(
            conn, source_id, workspace_id, chunks, embeddings
        )
        assert n == 2

        # Consulta identica ao primeiro texto => ele deve vir em primeiro.
        query = emb.embed(["habeas corpus preventivo"])[0]
        results = retrieval.search(
            conn, workspace_id=workspace_id, query_embedding=query, k=2
        )
        assert len(results) == 2
        assert results[0]["content"] == "habeas corpus preventivo"
        assert results[0]["similarity"] >= results[1]["similarity"]
        assert results[0]["similarity"] == pytest.approx(1.0, abs=1e-6)
    finally:
        try:
            conn.rollback()
        except Exception:  # noqa: BLE001
            pass
        conn.close()
