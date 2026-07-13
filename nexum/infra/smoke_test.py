"""Teste de integracao end-to-end da outbox -> relay (Pub/Sub fake).

Este teste NAO requer Docker para *coletar* sob o pytest: se Postgres/Redis nao
estiverem acessiveis, ele e marcado como SKIP (nao falha). Quando a infra esta
de pe (via `make up`), ele:

  1. conecta ao Postgres (psycopg) e ao Redis usando variaveis de ambiente;
  2. insere um CloudEvent real na `transactional_outbox`;
  3. roda `relay.drain_once` contra um publicador fake em memoria;
  4. assevera que a linha recebeu `published_at` e que o publicador capturou uma
     mensagem cuja `idempotencykey` casa com a inserida.

Rodar apenas este teste: `pytest nexum -m integration`.
"""

from __future__ import annotations

import json
import os
import uuid

import pytest

from nexum.cloudevents import CloudEvent, build_idempotency_key
from nexum.relay import worker

PG_DSN = os.environ.get(
    "NEXUM_OUTBOX_DSN", "postgresql://nexum:nexum@localhost:5432/nexum"
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
TOPIC = os.environ.get("NEXUM_PUBSUB_TOPIC", "nexum.artifact-events")


class CapturingPublisher:
    """Publicador em memoria compativel com o Protocol `Publisher` do relay."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, bytes]] = []

    def publish(self, topic: str, data: bytes) -> str:
        self.messages.append((topic, data))
        return f"fake-msg-{len(self.messages)}"


def _connect_or_skip():
    """Conecta a Postgres e Redis; faz `pytest.skip` se a infra estiver down."""

    try:
        import psycopg
        import redis
    except ImportError as exc:  # pragma: no cover - depende do ambiente
        pytest.skip(f"dependencias de infra ausentes: {exc}")

    try:
        conn = psycopg.connect(PG_DSN, connect_timeout=2)
    except Exception as exc:  # noqa: BLE001 - qualquer falha de conexao => skip
        pytest.skip(f"infra not up (postgres): {exc}")

    try:
        redis_client = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=2)
        redis_client.ping()
    except Exception as exc:  # noqa: BLE001
        conn.close()
        pytest.skip(f"infra not up (redis): {exc}")

    return conn, redis_client


@pytest.mark.integration
def test_outbox_relay_publishes_and_marks_row() -> None:
    conn, redis_client = _connect_or_skip()
    try:
        artifact_id = f"art_{uuid.uuid4()}"
        idempotency_key = build_idempotency_key(artifact_id, "SMOKE_TEST")
        event = CloudEvent(
            id=str(uuid.uuid4()),
            source="urn:nexum:smoke-test",
            type="br.nexum.artifact.integrity.alert.v1",
            subject=artifact_id,
            time="2026-07-13T00:00:00Z",
            correlationid=str(uuid.uuid4()),
            idempotencykey=idempotency_key,
            data={"artifact_id": artifact_id, "incident_reason": "smoke test"},
        )

        cur = conn.cursor()
        # Isola a passada: remove qualquer pendencia para garantir 1 captura.
        cur.execute(
            "DELETE FROM transactional_outbox WHERE published_at IS NULL"
        )
        cur.execute(
            "INSERT INTO transactional_outbox "
            "(aggregate_id, event_type, payload, published_at) "
            "VALUES (%s, %s, %s, NULL) RETURNING id",
            (
                artifact_id,
                event.type,
                json.dumps(event.model_dump()),
            ),
        )
        row_id = cur.fetchone()[0]
        conn.commit()

        publisher = CapturingPublisher()
        published = worker.drain_once(conn, publisher, TOPIC)

        assert published == 1
        assert len(publisher.messages) == 1

        topic, data = publisher.messages[0]
        assert topic == TOPIC
        captured = json.loads(data.decode("utf-8"))
        assert captured["idempotencykey"] == idempotency_key

        # A linha deve ter sido marcada como publicada na mesma transacao.
        cur.execute(
            "SELECT published_at FROM transactional_outbox WHERE id = %s",
            (row_id,),
        )
        published_at = cur.fetchone()[0]
        assert published_at is not None
    finally:
        try:
            conn.rollback()
        except Exception:  # noqa: BLE001
            pass
        conn.close()
        redis_client.close()
