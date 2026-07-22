"""Camada de normalizacao pgvector do NEXUM (busca semantica/RAG).

Este pacote e GREENFIELD: entrega o nucleo de normalizacao vetorial, o schema
pgvector (`sources`/`chunks` + indice HNSW cosseno), o chunking app-side de
texto juridico, o contrato `Embedder` (com fake deterministico para testes) e o
construtor de query KNN (`<=>`). As rotas HTTP (/sources, /conversations,
/messages) e o embedder real (Gemini/Vertex) NAO fazem parte deste pacote — ver
docs/schemas/NEXUM_pgvector.md.

REGRA CENTRAL: vetores sao L2-normalizados na ESCRITA. Com vetores unitarios, a
distancia de cosseno equivale a `1 - produto_interno`, casando exatamente com o
operador `<=>` (`vector_cosine_ops`) do pgvector sob o indice HNSW.
"""

from __future__ import annotations

from nexum.engine.chunking import Chunk, chunk_text
from nexum.engine.embeddings import (
    DeterministicFakeEmbedder,
    Embedder,
    build_embedder_from_env,
)
from nexum.engine.retrieval import SEARCH_SQL, search, upsert_chunks
from nexum.engine.vectors import (
    EMBEDDING_DIM,
    cosine_distance,
    cosine_similarity,
    l2_normalize,
    to_pgvector_literal,
    validate_dim,
)

__all__ = [
    "EMBEDDING_DIM",
    "l2_normalize",
    "validate_dim",
    "cosine_distance",
    "cosine_similarity",
    "to_pgvector_literal",
    "Chunk",
    "chunk_text",
    "Embedder",
    "DeterministicFakeEmbedder",
    "build_embedder_from_env",
    "SEARCH_SQL",
    "search",
    "upsert_chunks",
]
