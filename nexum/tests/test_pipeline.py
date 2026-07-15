"""Testes do pipeline forense NEXUM usando apenas fakes (sem rede/DB)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pytest
from fastapi.testclient import TestClient

from nexum.alerting import dispatcher as dispatcher_module
from nexum.cloudevents import CloudEvent, Priority, build_idempotency_key
from nexum.consumer.app import IDEMPOTENCY_PREFIX, create_app
from nexum.relay import replay, worker

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


def _load(name: str) -> CloudEvent:
    raw = json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))
    return CloudEvent(**raw)


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #
class FakeRedis:
    """Redis fake respaldado por dict, com suporte a SET NX + EX e DEL."""

    def __init__(self) -> None:
        self.store: dict[str, Any] = {}

    def set(
        self,
        name: str,
        value: Any,
        *,
        nx: bool = False,
        ex: Optional[int] = None,
    ) -> Optional[bool]:
        if nx and name in self.store:
            return None
        self.store[name] = value
        return True

    def delete(self, *names: str) -> int:
        removed = 0
        for name in names:
            if name in self.store:
                del self.store[name]
                removed += 1
        return removed


class FakeCursor:
    def __init__(self, rows: list[tuple]) -> None:
        self._rows = rows
        self.executed: list[tuple] = []
        self.updates: list[tuple] = []
        self.inserts: list[tuple] = []

    def execute(self, sql: str, params: tuple = ()) -> None:
        self.executed.append((sql, params))
        if sql.startswith("UPDATE"):
            self.updates.append(params)
        if sql.startswith("INSERT"):
            self.inserts.append(params)

    def fetchall(self) -> list[tuple]:
        return self._rows

    def close(self) -> None:
        pass


class FakeConn:
    def __init__(self, rows: list[tuple]) -> None:
        self._cursor = FakeCursor(rows)
        self.committed = False
        self.rolled_back = False

    def cursor(self) -> FakeCursor:
        return self._cursor

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


class FakePublisher:
    def __init__(self) -> None:
        self.published: list[tuple[str, bytes]] = []

    def publish(self, topic: str, data: bytes) -> str:
        self.published.append((topic, data))
        return f"msg-{len(self.published)}"


# --------------------------------------------------------------------------- #
# Schemas -> CloudEvent + prioridade
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "filename,expected",
    [
        ("artifact_quarantined.json", Priority.P2),
        ("integrity_alert.json", Priority.P1),
        ("compensate_pipeline.json", Priority.P1),
        ("replay_executed.json", Priority.P3),
    ],
)
def test_schema_parses_and_has_priority(filename: str, expected: Priority) -> None:
    event = _load(filename)
    assert event.specversion == "1.0"
    assert event.priority() is expected


def test_build_idempotency_key() -> None:
    assert (
        build_idempotency_key("art_123", "QUARANTINED")
        == "art_123:QUARANTINED"
    )


# --------------------------------------------------------------------------- #
# Consumidor idempotente
# --------------------------------------------------------------------------- #
def test_consumer_dedup() -> None:
    fake_redis = FakeRedis()
    app = create_app(fake_redis, dispatcher_module)
    client = TestClient(app)

    payload = json.loads(
        (SCHEMAS_DIR / "artifact_quarantined.json").read_text(encoding="utf-8")
    )

    first = client.post("/events", json=payload)
    assert first.status_code == 200
    assert first.json()["status"] == "accepted"

    second = client.post("/events", json=payload)
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"
    assert second.json()["idempotencykey"] == payload["idempotencykey"]


def test_healthz() -> None:
    app = create_app(FakeRedis(), dispatcher_module)
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


class FlakyDispatcher:
    """Dispatcher que falha na primeira chamada e funciona nas seguintes."""

    def __init__(self) -> None:
        self.calls = 0

    def dispatch(self, event: CloudEvent) -> dict:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("pagerduty indisponivel")
        return dispatcher_module.dispatch(event)


def test_consumer_releases_key_when_p1_dispatch_fails() -> None:
    """Falha de dispatch P1 nao pode marcar o evento como processado.

    Sem a liberacao da chave, a redelivery seria descartada como duplicata e
    um alerta critico de integridade se perderia para sempre.
    """

    fake_redis = FakeRedis()
    flaky = FlakyDispatcher()
    app = create_app(fake_redis, flaky)
    client = TestClient(app)

    payload = json.loads(
        (SCHEMAS_DIR / "integrity_alert.json").read_text(encoding="utf-8")
    )
    key = f"{IDEMPOTENCY_PREFIX}{payload['idempotencykey']}"

    first = client.post("/events", json=payload)
    assert first.status_code == 500
    assert first.json()["status"] == "dispatch_failed"
    # Chave liberada: a redelivery deve ser reprocessada, nao descartada.
    assert key not in fake_redis.store

    retry = client.post("/events", json=payload)
    assert retry.status_code == 200
    assert retry.json()["status"] == "accepted"
    assert flaky.calls == 2
    assert key in fake_redis.store

    # Apos o sucesso, novas entregas do mesmo evento voltam a ser duplicatas.
    third = client.post("/events", json=payload)
    assert third.json()["status"] == "duplicate"
    assert flaky.calls == 2


# --------------------------------------------------------------------------- #
# Dispatcher
# --------------------------------------------------------------------------- #
def test_dispatcher_maps_p1_integrity_alert() -> None:
    event = _load("integrity_alert.json")
    result = dispatcher_module.dispatch(event)

    assert result["siem"]["event.severity"] == 1
    assert result["pagerduty"] is not None
    assert result["pagerduty"]["payload"]["severity"] == "critical"
    assert result["pagerduty"]["dedup_key"] == event.idempotencykey


def test_dispatcher_p3_no_pagerduty() -> None:
    event = _load("replay_executed.json")
    result = dispatcher_module.dispatch(event)
    assert result["siem"]["event.severity"] == 5
    assert result["pagerduty"] is None


# --------------------------------------------------------------------------- #
# Relay drain_once
# --------------------------------------------------------------------------- #
def test_relay_drain_once() -> None:
    rows = [
        (1, '{"id": "a"}', 0),
        (2, '{"id": "b"}', 0),
    ]
    conn = FakeConn(rows)
    publisher = FakePublisher()

    count = worker.drain_once(conn, publisher, "nexum.artifact-events")

    assert count == 2
    assert len(publisher.published) == 2
    assert conn.committed is True
    assert conn.rolled_back is False
    # Duas linhas marcadas como publicadas (UPDATE por linha).
    assert len(conn.cursor().updates) == 2


class PoisonPublisher:
    """Publisher que falha para payloads contendo o marcador `poison`."""

    def __init__(self) -> None:
        self.published: list[tuple[str, bytes]] = []

    def publish(self, topic: str, data: bytes) -> str:
        if b"poison" in data:
            raise RuntimeError("payload rejeitado pelo broker")
        self.published.append((topic, data))
        return f"msg-{len(self.published)}"


def test_relay_poison_row_does_not_block_batch() -> None:
    """Uma linha envenenada nao derruba o lote nem bloqueia a fila."""

    rows = [
        (1, '{"id": "a"}', 0),
        (2, '{"id": "poison"}', 0),
        (3, '{"id": "c"}', 0),
    ]
    conn = FakeConn(rows)
    publisher = PoisonPublisher()

    count = worker.drain_once(conn, publisher, "nexum.artifact-events")

    # As duas linhas saudaveis publicam; a envenenada e isolada.
    assert count == 2
    assert len(publisher.published) == 2
    assert conn.committed is True
    assert conn.rolled_back is False

    cursor = conn.cursor()
    # 2 MARK_PUBLISHED + 1 RECORD_FAILURE.
    assert len(cursor.updates) == 3
    failure_calls = [
        params
        for sql, params in cursor.executed
        if sql == worker.RECORD_FAILURE_SQL
    ]
    assert len(failure_calls) == 1
    error_text, max_attempts, _now, row_id = failure_calls[0]
    assert "payload rejeitado pelo broker" in error_text
    assert max_attempts == worker.DEFAULT_MAX_ATTEMPTS
    assert row_id == 2


def test_relay_record_failure_carries_max_attempts_for_dead_letter() -> None:
    """O limite configurado chega a UPDATE que decide o dead-letter no banco."""

    rows = [(9, '{"id": "poison"}', 2)]
    conn = FakeConn(rows)

    count = worker.drain_once(
        conn, PoisonPublisher(), "nexum.artifact-events", max_attempts=3
    )

    assert count == 0
    failure_calls = [
        params
        for sql, params in conn.cursor().executed
        if sql == worker.RECORD_FAILURE_SQL
    ]
    assert len(failure_calls) == 1
    _error, max_attempts, _now, row_id = failure_calls[0]
    assert max_attempts == 3
    assert row_id == 9
    # A query filtra a DLQ da drenagem e o CASE faz o dead-letter atomico.
    assert "dead_lettered_at IS NULL" in worker.SELECT_BATCH_SQL
    assert "CASE WHEN attempts + 1 >= %s" in worker.RECORD_FAILURE_SQL


# --------------------------------------------------------------------------- #
# Replay da DLQ (br.nexum.infra.replay.executed.v1)
# --------------------------------------------------------------------------- #
def test_replay_requeues_dead_letters_and_audits() -> None:
    dead_payload = {"id": "evt-1", "isreplay": False, "type": "x"}
    rows = [(7, json.dumps(dead_payload))]
    conn = FakeConn(rows)

    count = replay.replay_dead_letters(
        conn,
        operator_id="MATRICULA_TESTE_01",
        justification="Conexao downstream reestabelecida.",
    )

    assert count == 1
    assert conn.committed is True
    cursor = conn.cursor()

    # Re-enfileiramento: payload volta marcado isreplay=true.
    requeue_calls = [
        params
        for sql, params in cursor.executed
        if sql == replay.REQUEUE_SQL
    ]
    assert len(requeue_calls) == 1
    requeued_payload, row_id = requeue_calls[0]
    assert row_id == 7
    assert json.loads(requeued_payload)["isreplay"] is True

    # Auditoria: CloudEvent do catalogo inserido na propria outbox.
    assert len(cursor.inserts) == 1
    subject, event_type, audit_json = cursor.inserts[0]
    assert event_type == replay.REPLAY_EXECUTED_TYPE
    audit = CloudEvent(**json.loads(audit_json))
    assert audit.subject == subject
    assert audit.operatorid == "MATRICULA_TESTE_01"
    assert audit.isreplay is True
    assert audit.priority() is Priority.P3
    assert audit.idempotencykey.endswith(":REPLAY_EXECUTED")
    assert audit.data["replayed_row_ids"] == [7]
    assert audit.data["count"] == 1
    assert audit.data["justification"] == "Conexao downstream reestabelecida."


def test_replay_empty_dlq_inserts_no_audit() -> None:
    conn = FakeConn([])

    count = replay.replay_dead_letters(conn, operator_id="system")

    assert count == 0
    assert conn.cursor().inserts == []
