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
from nexum.relay import replay, worker

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


class ExplodingPublisher:
    """Publicador que sempre falha (simula broker/downstream indisponivel)."""

    def publish(self, topic: str, data: bytes) -> str:
        raise RuntimeError("downstream indisponivel")


@pytest.mark.integration
def test_dead_letter_and_replay_cycle() -> None:
    """Ciclo completo da DLQ: falha -> dead-letter -> replay -> drenagem.

    1. insere um CloudEvent na outbox;
    2. drena com publicador quebrado e max_attempts=1 => linha vai a DLQ
       (attempts=1, last_error preenchido, dead_lettered_at NOT NULL);
    3. confirma que a linha dead-lettered fica FORA da drenagem;
    4. replay autorizado re-enfileira (isreplay=true) + insere o evento de
       auditoria br.nexum.infra.replay.executed.v1 na outbox;
    5. nova drenagem publica o evento replayed E a auditoria.
    """

    conn, redis_client = _connect_or_skip()
    try:
        artifact_id = f"art_{uuid.uuid4()}"
        idempotency_key = build_idempotency_key(artifact_id, "DLQ_CYCLE")
        event = CloudEvent(
            id=str(uuid.uuid4()),
            source="urn:nexum:smoke-test",
            type="br.nexum.artifact.integrity.alert.v1",
            subject=artifact_id,
            time="2026-07-15T00:00:00Z",
            correlationid=str(uuid.uuid4()),
            idempotencykey=idempotency_key,
            data={"artifact_id": artifact_id, "incident_reason": "dlq cycle"},
        )

        cur = conn.cursor()
        # Isola a passada (inclui linhas dead-lettered de execucoes anteriores,
        # que tambem tem published_at NULL).
        cur.execute(
            "DELETE FROM transactional_outbox WHERE published_at IS NULL"
        )
        cur.execute(
            "INSERT INTO transactional_outbox "
            "(aggregate_id, event_type, payload, published_at) "
            "VALUES (%s, %s, %s, NULL) RETURNING id",
            (artifact_id, event.type, json.dumps(event.model_dump())),
        )
        row_id = cur.fetchone()[0]
        conn.commit()

        # (2) Publicador quebrado + max_attempts=1 => dead-letter imediato.
        published = worker.drain_once(
            conn, ExplodingPublisher(), TOPIC, max_attempts=1
        )
        assert published == 0

        cur.execute(
            "SELECT attempts, last_error, dead_lettered_at "
            "FROM transactional_outbox WHERE id = %s",
            (row_id,),
        )
        attempts, last_error, dead_lettered_at = cur.fetchone()
        assert attempts == 1
        assert "downstream indisponivel" in last_error
        assert dead_lettered_at is not None

        # (3) Na DLQ, a linha fica fora da drenagem.
        quiet = CapturingPublisher()
        assert worker.drain_once(conn, quiet, TOPIC) == 0
        assert quiet.messages == []

        # (4) Replay autorizado.
        replayed = replay.replay_dead_letters(
            conn,
            operator_id="MATRICULA_SMOKE_01",
            justification="smoke: downstream reestabelecido",
        )
        assert replayed == 1

        # (5) Drenagem publica o evento replayed + a auditoria do replay.
        publisher = CapturingPublisher()
        published = worker.drain_once(conn, publisher, TOPIC)
        assert published == 2

        decoded = [
            json.loads(data.decode("utf-8"))
            for _topic, data in publisher.messages
        ]
        replayed_event = next(
            d for d in decoded if d["idempotencykey"] == idempotency_key
        )
        assert replayed_event["isreplay"] is True

        audit_event = next(
            d for d in decoded if d["type"] == replay.REPLAY_EXECUTED_TYPE
        )
        assert audit_event["operatorid"] == "MATRICULA_SMOKE_01"
        assert audit_event["data"]["replayed_row_ids"] == [row_id]
    finally:
        try:
            conn.rollback()
        except Exception:  # noqa: BLE001
            pass
        conn.close()
        redis_client.close()
