-- NEXUM TIER 0 — DDL da Transactional Outbox (Postgres)
--
-- A coluna `payload` (JSONB) carrega o CloudEvent v1.0 serializado. O nome da
-- coluna deve casar EXATAMENTE com a query do relay em nexum/relay/worker.py:
--   SELECT id, payload FROM transactional_outbox
--   WHERE published_at IS NULL ORDER BY created_at
--   FOR UPDATE SKIP LOCKED LIMIT %s
-- e com MARK_PUBLISHED_SQL: UPDATE ... SET published_at = %s WHERE id = %s

CREATE TABLE IF NOT EXISTS transactional_outbox (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aggregate_id  TEXT NOT NULL,            -- artifact_id do CloudEvent
    event_type    TEXT NOT NULL,            -- CloudEvent `type`
    payload       JSONB NOT NULL,           -- CloudEvent v1.0 serializado
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at  TIMESTAMPTZ NULL          -- NULL => aguardando publicacao
);

-- Indice parcial que acelera a query de drenagem do relay (somente linhas
-- ainda nao publicadas, ordenadas por created_at).
CREATE INDEX IF NOT EXISTS idx_outbox_unpublished
    ON transactional_outbox (created_at)
    WHERE published_at IS NULL;

-- --------------------------------------------------------------------------- #
-- Seeds: dois CloudEvents reais (integridade P1 e quarentena P2), ainda nao
-- publicados (published_at NULL), prontos para o relay drenar.
-- --------------------------------------------------------------------------- #
INSERT INTO transactional_outbox (aggregate_id, event_type, payload, published_at)
VALUES
(
    'art_9912a773-44bb-4e90-ba33-8c437a346511',
    'br.nexum.artifact.integrity.alert.v1',
    '{
      "specversion": "1.0",
      "id": "fc529881-19ab-411a-8bb7-18b76c8c4a52",
      "source": "urn:nexum:artifact-pipeline:integrity-watcher",
      "type": "br.nexum.artifact.integrity.alert.v1",
      "subject": "art_9912a773-44bb-4e90-ba33-8c437a346511",
      "time": "2026-07-02T03:36:12Z",
      "datacontenttype": "application/json",
      "correlationid": "a988bc2a-1433-4f9e-bd83-112cbfa290cc",
      "idempotencykey": "art_9912a773-44bb-4e90-ba33-8c437a346511:SUSPECT_INTEGRITY",
      "isreplay": false,
      "operatorid": "system",
      "data": {
        "artifact_id": "art_9912a773-44bb-4e90-ba33-8c437a346511",
        "detected_at_state": "SCAN_PENDING",
        "expected_hash": "8f43c22198fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852c001",
        "computed_hash": "2a11b99368fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852a332",
        "incident_reason": "Divergencia de hash criptografico pos-upload local. Bloqueando transacoes futuras do NPU correspondente."
      }
    }'::jsonb,
    NULL
),
(
    'art_883c4290-0f2d-45db-99e0-05047b19dfb4',
    'br.nexum.artifact.quarantined.v1',
    '{
      "specversion": "1.0",
      "id": "e0b4b241-7db9-4672-911b-c6b7ef14cf39",
      "source": "urn:nexum:artifact-pipeline:scanner",
      "type": "br.nexum.artifact.quarantined.v1",
      "subject": "art_883c4290-0f2d-45db-99e0-05047b19dfb4",
      "time": "2026-07-02T03:35:00Z",
      "datacontenttype": "application/json",
      "correlationid": "c76fb9a2-dc18-4e89-8d14-3403d159a68a",
      "idempotencykey": "art_883c4290-0f2d-45db-99e0-05047b19dfb4:QUARANTINED",
      "isreplay": false,
      "operatorid": "system",
      "data": {
        "artifact_id": "art_883c4290-0f2d-45db-99e0-05047b19dfb4",
        "npu_masked": "5001234-[CPF_MASKED_6a7f]-2026-8-16-0001",
        "original_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "quarantine_bucket_uri": "gs://nexum-forensic-quarantine/isolated/art_883c4290-0f2d-45db-99e0-05047b19dfb4.pdf",
        "incident_reason": "Assinatura positiva para Trojan.Generic.HEUR na esteira de pre-sanitizacao."
      }
    }'::jsonb,
    NULL
);
