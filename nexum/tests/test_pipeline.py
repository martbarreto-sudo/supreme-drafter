"""Testes do pipeline forense NEXUM usando apenas fakes (sem rede/DB)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pytest
from fastapi.testclient import TestClient

from nexum.alerting import dispatcher as dispatcher_module
from nexum.cloudevents import CloudEvent, Priority, build_idempotency_key
from nexum.consumer.app import create_app
from nexum.relay import worker

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


def _load(name: str) -> CloudEvent:
    raw = json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))
    return CloudEvent(**raw)


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #
class FakeRedis:
    """Redis fake respaldado por dict, com suporte a SET NX + EX."""

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


class FakeCursor:
    def __init__(self, rows: list[tuple]) -> None:
        self._rows = rows
        self.executed: list[tuple] = []
        self.updates: list[tuple] = []

    def execute(self, sql: str, params: tuple = ()) -> None:
        self.executed.append((sql, params))
        if sql.startswith("UPDATE"):
            self.updates.append(params)

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
        (1, '{"id": "a"}'),
        (2, '{"id": "b"}'),
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
