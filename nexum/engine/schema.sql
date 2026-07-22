-- NEXUM — DDL da camada de normalizacao pgvector (busca semantica/RAG).
--
-- SEPARADO do schema da outbox (nexum/infra/schema.sql). No compose/CI este
-- arquivo e carregado DEPOIS do schema da outbox (ex.: 02-engine.sql) para que
-- a extensao `vector` e as tabelas de RAG coexistam com a `transactional_outbox`.
--
-- CONTRATO DE PAYLOAD: os nomes de colunas casam com docs/api-spec.json
-- (/sources -> s3_key, workspace_id, source_type, metadata{npu,tribunal,
-- data_documento}, status, clamav_result).
--
-- DIMENSAO DO EMBEDDING: o literal `vector(768)` abaixo e o DEFAULT COMMITADO e
-- DEVE casar com a env `NEXUM_EMBEDDING_DIM` (default 768) lida por
-- nexum/engine/vectors.py. SQL nao le variaveis de ambiente: alterar a dimensao
-- exige REGENERAR este DDL (trocar 768 nos dois literais `vector(...)`) e
-- reindexar. Divergencia entre a dim do embedder e a coluna causa erro de INSERT.

CREATE EXTENSION IF NOT EXISTS vector;

-- --------------------------------------------------------------------------- #
-- sources: uma fonte ingerida do PJe (peticao/decisao/acordao/laudo/midia).
-- Espelha o corpo do POST /sources da api-spec.
-- --------------------------------------------------------------------------- #
CREATE TABLE IF NOT EXISTS sources (
    source_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  UUID NOT NULL,
    s3_key        TEXT NOT NULL,
    source_type   TEXT NOT NULL
        CHECK (source_type IN ('peticao','decisao','acordao','laudo','midia')),
    -- metadata.{npu,tribunal,data_documento} do payload /sources.
    npu           TEXT,
    tribunal      TEXT,
    data_documento DATE,
    status        TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued','processing','indexed')),
    clamav_result TEXT
        CHECK (clamav_result IN ('clean','quarantined')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- --------------------------------------------------------------------------- #
-- chunks: fragmentos indexados de uma source, com embedding L2-normalizado.
-- `workspace_id` e DENORMALIZADO aqui para permitir filtro/RLS por tenant sem
-- JOIN em cada consulta KNN (o filtro entra no WHERE da busca).
-- `fls_ref` preserva a folha (fls. N) conforme a doutrina Deep Hunter.
-- --------------------------------------------------------------------------- #
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id    UUID NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL,          -- denormalizado p/ RLS/filtragem
    chunk_index  INT NOT NULL,
    content      TEXT NOT NULL,
    fls_ref      TEXT,                    -- referencia de folha (ex.: "fls. 42")
    token_count  INT,
    embedding    vector(768) NOT NULL,    -- DEVE casar com NEXUM_EMBEDDING_DIM
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_id, chunk_index)
);

-- Indice HNSW para busca aproximada por cosseno. `vector_cosine_ops` casa com o
-- operador `<=>` usado em nexum/engine/retrieval.py (SEARCH_SQL). Como os
-- vetores sao L2-normalizados na escrita, cosseno == 1 - produto_interno.
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
    ON chunks USING hnsw (embedding vector_cosine_ops);

-- Indice de apoio para o filtro por tenant no WHERE da busca KNN.
CREATE INDEX IF NOT EXISTS idx_chunks_workspace
    ON chunks (workspace_id);

-- --------------------------------------------------------------------------- #
-- RLS (isolamento de tenant): consistente com a api-spec (Row-Level Security
-- automatico por workspace). NAO habilitado aqui para manter o greenfield
-- simples e testavel; em producao adicionar-se-ia:
--   ALTER TABLE chunks  ENABLE ROW LEVEL SECURITY;
--   ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
--   CREATE POLICY tenant_isolation ON chunks
--       USING (workspace_id = current_setting('nexum.workspace_id')::uuid);
-- (idem para sources). Enquanto isso, a busca sempre filtra por workspace_id.
-- --------------------------------------------------------------------------- #
