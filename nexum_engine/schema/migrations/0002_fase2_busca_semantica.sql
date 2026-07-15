-- ============================================================================
-- Migração 0002 — Fase 2: busca semântica (pgvector) na base verificada
--
-- Aplicar no Supabase (SQL Editor, como OWNER/service role) DEPOIS de
-- schema/precedentes.sql. Idempotente.
--
-- N = 768: dimensão do modelo de embedding escolhido pelo operador no
-- gatilho HITL (padrão da família text-embedding/gecko do Vertex AI).
-- Se o modelo escolhido tiver outra dimensão, ajustar AQUI e no parâmetro
-- `dimensao` do VertexEmbedAdapter antes da carga de vetores.
-- ============================================================================

-- Extensão pgvector nativa do Supabase.
CREATE EXTENSION IF NOT EXISTS vector;

-- Coluna de embeddings (NULL até o backfill — a busca semântica ignora
-- registros sem vetor e o fallback por tags cobre o intervalo).
ALTER TABLE precedentes_verificados
    ADD COLUMN IF NOT EXISTS vetor_semantico vector(768);

-- Índice HNSW para distância de cosseno.
-- m=16, ef_construction=64: equilíbrio entre tempo de build e recall.
CREATE INDEX IF NOT EXISTS idx_precedentes_vetor
    ON precedentes_verificados
    USING hnsw (vetor_semantico vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ----------------------------------------------------------------------------
-- Sem função RPC: a engine consulta via asyncpg (DatabasePort) com SQL
-- parametrizado usando o operador <=> diretamente — ver
-- nexum_engine/verdade/fontes.py::FonteSupabase.buscar_por_semelhanca.
--
-- Backfill dos vetores (pós-HITL, como service role — a RLS nega escrita
-- aos papéis da engine de propósito): para cada linha citável, gerar o
-- embedding de (tese || ementa) com o MESMO modelo configurado no
-- VertexEmbedAdapter e:
--   UPDATE precedentes_verificados SET vetor_semantico = $1::vector
--    WHERE numero_normalizado = $2;
-- ----------------------------------------------------------------------------
