-- ============================================================================
-- Migração 0003 — Fase 3: filtros de metadados na busca semântica
--
-- Aplicar no Supabase (SQL Editor, como OWNER/service role) DEPOIS de
-- 0002_fase2_busca_semantica.sql. Idempotente.
--
-- A busca vetorial passa a aceitar filtros opcionais (tribunal, tema) na
-- PRÓPRIA consulta — ver fontes.py::FonteSupabase.buscar_por_semelhanca.
-- No pgvector, WHERE em consulta HNSW é PÓS-filtro: o índice devolve os
-- candidatos de ef_search e o filtro corta depois; com filtros seletivos
-- o top-K pode voltar incompleto (recall degradado). As duas medidas
-- abaixo atacam exatamente isso.
-- ============================================================================

-- Índices B-Tree case-insensitivos para os filtros (a comparação no SQL é
-- upper(coluna) = upper($n), a mesma semântica do _passa_filtros das
-- fontes em Python). Também servem a caminhos não-vetoriais.
CREATE INDEX IF NOT EXISTS idx_precedentes_tribunal_ci
    ON precedentes_verificados (upper(tribunal));
CREATE INDEX IF NOT EXISTS idx_precedentes_tema_ci
    ON precedentes_verificados (upper(tema));

-- pgvector >= 0.8: varredura iterativa — o HNSW continua varrendo até o
-- LIMIT ser satisfeito quando o pós-filtro descarta candidatos. Fixado no
-- NÍVEL DO BANCO de propósito: o DatabasePort trabalha sobre pool, e GUC
-- de sessão por conexão não teria garantia nenhuma. `relaxed_order`
-- maximiza o recall e pode devolver vizinhos quase-empatados levemente
-- fora de ordem; se a ordenação estrita importar mais que o recall,
-- trocar por `strict_order`.
DO $$
BEGIN
    EXECUTE format(
        'ALTER DATABASE %I SET hnsw.iterative_scan = relaxed_order',
        current_database()
    );
    RAISE NOTICE 'hnsw.iterative_scan = relaxed_order fixado no banco.';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE
        'hnsw.iterative_scan indisponível (pgvector < 0.8?): com filtros '
        'muito seletivos o top-K pode voltar incompleto; mitigar elevando '
        'hnsw.ef_search ou atualizando a extensão. Erro: %', SQLERRM;
END $$;

-- Após aplicar: rode a validação de recall (utilitário de operador)
-- nexum_engine/verdade/validar_recall.py — inclusive comparando execuções
-- com e sem filtros seletivos na sua base real.
