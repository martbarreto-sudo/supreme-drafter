# nexum/engine — camada de normalizacao pgvector (busca semantica / RAG)

GREENFIELD. Entrega o **nucleo de normalizacao vetorial + schema + recuperacao**
para o RAG do NEXUM. As rotas HTTP (`/sources`, `/conversations`,
`/messages/stream`) e o embedder real (Gemini/Vertex) **NAO** fazem parte deste
pacote — sao o proximo passo.

As **regras de normalizacao** (por que L2-normalize na escrita + cosseno + HNSW,
dimensao configuravel, politica de chunking, mapeamento para a api-spec) estao em
[`docs/schemas/NEXUM_pgvector.md`](../../docs/schemas/NEXUM_pgvector.md).

## Modulos

| Arquivo | Responsabilidade |
| --- | --- |
| `schema.sql` | `CREATE EXTENSION vector` + tabelas `sources`/`chunks` + indice HNSW cosseno. Carregado apos a outbox (`02-engine.sql`). |
| `vectors.py` | REGRA CENTRAL: `l2_normalize` (unitario na escrita; erro em vetor zero), `cosine_distance`/`cosine_similarity` (Python puro), `to_pgvector_literal`. `EMBEDDING_DIM` (env `NEXUM_EMBEDDING_DIM`, default 768). |
| `chunking.py` | `chunk_text` — janelas ~`target_tokens` com overlap, fronteiras de sentenca, extracao de `fls.`. Proxy de tokens por espacos. |
| `embeddings.py` | `Embedder` Protocol + `DeterministicFakeEmbedder` (sha256, sem rede) + `build_embedder_from_env`. |
| `retrieval.py` | `SEARCH_SQL` (KNN por `<=>`), `search`, `upsert_chunks` (idempotente `ON CONFLICT`; normaliza na escrita). |
| `integration_test.py` | `@pytest.mark.integration`; upsert + search contra Postgres pgvector real. SKIP limpo sem DB/extensao. |

## Regra central (resumo)

Vetores sao **L2-normalizados na escrita**. Com vetores unitarios,
`cosine_distance == 1 - dot`, casando com o operador `<=>`
(`vector_cosine_ops`) do pgvector sob o indice HNSW.

## Testes

```bash
# unitarios (sem DB/rede), deterministicos
python3 -m pytest nexum -q -m "not integration"
# integracao (requer Postgres pgvector; SKIP limpo se ausente)
python3 -m pytest nexum -q -m integration
```
