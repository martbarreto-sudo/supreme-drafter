-- ============================================================================
-- precedentes_verificados — base de precedentes do loop de verdade NEXUM
--
-- Schema derivado campo a campo da base MINDJUS real
-- (warroom-tigre/mindjus_data/*.json), incluindo o mecanismo de quarentena.
-- Aplicar no Supabase (SQL Editor) no gatilho HITL, antes de injetar o
-- asyncpg.Pool no AsyncpgAdapter.
-- ============================================================================

CREATE TABLE IF NOT EXISTS precedentes_verificados (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    numero               TEXT NOT NULL,               -- "HC 598.051/SP", "Súmula 444/STJ"
    numero_normalizado   TEXT NOT NULL UNIQUE,        -- forma canônica (ver nexum_engine.verdade.normalizar_citacao)
    tese                 TEXT NOT NULL,
    tribunal             TEXT NOT NULL DEFAULT '',
    relator              TEXT NOT NULL DEFAULT '',
    data_julgamento      TEXT NOT NULL DEFAULT '',
    ementa               TEXT NOT NULL DEFAULT '',
    resultado            TEXT NOT NULL DEFAULT '',
    tags                 TEXT[] NOT NULL DEFAULT '{}',
    relevancia           TEXT NOT NULL DEFAULT '',
    -- Doutrina 100/100: sem fonte oficial o registro nem deveria entrar;
    -- o CHECK só admite exceção quando explicitamente em quarentena.
    fonte_verificacao    TEXT NOT NULL DEFAULT '',
    tema                 TEXT NOT NULL DEFAULT '',
    verificacao_pendente BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_quarentena    TEXT NOT NULL DEFAULT '',
    criado_em            TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em        TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fonte_ou_quarentena CHECK (
        fonte_verificacao <> '' OR verificacao_pendente
    ),
    CONSTRAINT quarentena_motivada CHECK (
        NOT verificacao_pendente OR motivo_quarentena <> ''
    )
);

CREATE INDEX IF NOT EXISTS idx_precedentes_tags
    ON precedentes_verificados USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_precedentes_tema
    ON precedentes_verificados (tema);

-- Fase 2 (busca semântica): habilitar pgvector e preencher via EmbedderPort.
-- CREATE EXTENSION IF NOT EXISTS vector;
-- ALTER TABLE precedentes_verificados ADD COLUMN embedding vector(768);

-- ----------------------------------------------------------------------------
-- Row-Level Security: leitura só do que é citável; escrita nunca pelo papel
-- da engine (promoção de precedente é ato humano/pipeline de verificação).
-- ----------------------------------------------------------------------------
ALTER TABLE precedentes_verificados ENABLE ROW LEVEL SECURITY;

CREATE POLICY leitura_apenas_citaveis ON precedentes_verificados
    FOR SELECT
    USING (fonte_verificacao <> '' AND NOT verificacao_pendente);

-- Nenhuma policy de INSERT/UPDATE/DELETE para o papel da engine:
-- com RLS habilitado e sem policy, a escrita é negada por padrão.
