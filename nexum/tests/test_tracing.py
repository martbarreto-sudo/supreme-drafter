"""Testes unitarios de observabilidade (OpenTelemetry) do pipeline NEXUM.

Todos os spans sao capturados por um `InMemorySpanExporter` (sem rede, sem
collector). Nenhum teste e marcado como integration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pytest
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from nexum.alerting import dispatcher as dispatcher_module
from nexum.cloudevents import CloudEvent
from nexum.consumer.app import create_app
from nexum.observability import tracing
from nexum.relay import worker

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


def _load_raw(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


def _load_event(name: str) -> CloudEvent:
    return CloudEvent(**_load_raw(name))


@pytest.fixture()
def exporter() -> InMemorySpanExporter:
    """Registra um exportador em memoria como destino dos spans do teste."""

    exp = InMemorySpanExporter()
    tracing.configure_tracing_for_test(exp)
    exp.clear()
    yield exp
    exp.clear()


def _spans_named(exp: InMemorySpanExporter, name: str) -> list[Any]:
    return [s for s in exp.get_finished_spans() if s.name == name]


# --------------------------------------------------------------------------- #
# Fakes (DB-API / Redis) espelhando os do test_pipeline
# --------------------------------------------------------------------------- #
class FakeCursor:
    def __init__(self, rows: list[tuple]) -> None:
        self._rows = rows
        self.updates: list[tuple] = []

    def execute(self, sql: str, params: tuple = ()) -> None:
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


class FakeRedis:
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


# --------------------------------------------------------------------------- #
# Relay: relay.drain_once + relay.publish
# --------------------------------------------------------------------------- #
def test_relay_spans_carry_batch_and_message_attributes(
    exporter: InMemorySpanExporter,
) -> None:
    integrity = _load_raw("integrity_alert.json")
    quarantined = _load_raw("artifact_quarantined.json")
    rows = [
        (1, json.dumps(integrity), 0),
        (2, json.dumps(quarantined), 0),
    ]
    conn = FakeConn(rows)
    publisher = FakePublisher()

    count = worker.drain_once(conn, publisher, "nexum.artifact-events")

    assert count == 2

    batch_spans = _spans_named(exporter, "relay.drain_once")
    assert len(batch_spans) == 1
    assert batch_spans[0].attributes["messaging.batch.count"] == 2

    publish_spans = _spans_named(exporter, "relay.publish")
    assert len(publish_spans) == 2

    by_type = {s.attributes.get("nexum.event_type"): s for s in publish_spans}
    assert set(by_type) == {integrity["type"], quarantined["type"]}

    span = by_type[integrity["type"]]
    assert span.attributes["messaging.system"] == "gcp_pubsub"
    assert span.attributes["messaging.destination"] == "nexum.artifact-events"
    assert span.attributes["nexum.correlation_id"] == integrity["correlationid"]
    assert span.attributes["nexum.idempotency_key"] == integrity["idempotencykey"]


# --------------------------------------------------------------------------- #
# Consumidor: consumer.handle_event + nexum.is_duplicate
# --------------------------------------------------------------------------- #
def test_consumer_span_marks_duplicate_on_second_post(
    exporter: InMemorySpanExporter,
) -> None:
    app = create_app(FakeRedis(), dispatcher_module)
    client = TestClient(app)
    payload = _load_raw("artifact_quarantined.json")

    first = client.post("/events", json=payload)
    assert first.status_code == 200
    first_spans = _spans_named(exporter, "consumer.handle_event")
    assert len(first_spans) == 1
    assert first_spans[0].attributes["nexum.is_duplicate"] is False
    assert first_spans[0].attributes["nexum.event_type"] == payload["type"]
    assert first_spans[0].attributes["nexum.priority"] == "P2"

    exporter.clear()

    second = client.post("/events", json=payload)
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"
    dup_spans = _spans_named(exporter, "consumer.handle_event")
    assert len(dup_spans) == 1
    assert dup_spans[0].attributes["nexum.is_duplicate"] is True


# --------------------------------------------------------------------------- #
# Dispatcher: alerting.dispatch
# --------------------------------------------------------------------------- #
def test_dispatch_span_on_p1_event(exporter: InMemorySpanExporter) -> None:
    event = _load_event("integrity_alert.json")

    result = dispatcher_module.dispatch(event)
    assert result["pagerduty"] is not None  # contrato inalterado

    spans = _spans_named(exporter, "alerting.dispatch")
    assert len(spans) == 1
    assert spans[0].attributes["nexum.sink.siem"] == 1
    assert spans[0].attributes["nexum.sink.pagerduty"] == 1
    assert spans[0].attributes["nexum.priority"] == "P1"
