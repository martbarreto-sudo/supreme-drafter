"""Dispatcher de alertas P1: mapeamento para SIEM (ECS) e PagerDuty (Events v2).

Eventos P1 (integridade comprometida e compensacao de saga) sao roteados tanto
para o SIEM quanto para o PagerDuty. Demais prioridades vao apenas ao SIEM.
Os *sinks* sao injetados como callables, o que mantem o modulo testavel sem
qualquer chamada de rede.
"""

from __future__ import annotations

import os
from typing import Callable, Optional

from nexum.cloudevents import CloudEvent, Priority
from nexum.observability.tracing import TRACER


def _message_of(event: CloudEvent) -> str:
    """Extrai a mensagem humana do payload, com fallbacks previsiveis."""

    data = event.data or {}
    return (
        data.get("incident_reason")
        or data.get("compensation_trigger")
        or event.type
    )


def map_to_siem(event: CloudEvent) -> dict:
    """Mapeia o CloudEvent para um registro estruturado no estilo ECS."""

    is_p1 = event.priority() is Priority.P1
    return {
        "@timestamp": event.time,
        "event.kind": "alert",
        "event.dataset": "nexum.forensic",
        "event.severity": 1 if is_p1 else 5,
        "nexum.artifact_id": event.subject,
        "nexum.correlation_id": event.correlationid,
        "nexum.type": event.type,
        "message": _message_of(event),
        "labels": {
            "idempotencykey": event.idempotencykey,
            "operatorid": event.operatorid,
            "isreplay": event.isreplay,
        },
    }


def map_to_pagerduty(event: CloudEvent) -> dict:
    """Mapeia o CloudEvent para um payload da PagerDuty Events API v2."""

    is_p1 = event.priority() is Priority.P1
    routing_key = os.environ.get(
        "NEXUM_PAGERDUTY_ROUTING_KEY", "PLACEHOLDER_ROUTING_KEY"
    )
    return {
        "routing_key": routing_key,
        "event_action": "trigger",
        "dedup_key": event.idempotencykey,
        "payload": {
            "summary": _message_of(event),
            "source": event.source,
            "severity": "critical" if is_p1 else "warning",
            "custom_details": event.data,
        },
    }


def dispatch(
    event: CloudEvent,
    siem_sink: Optional[Callable[[dict], None]] = None,
    pagerduty_sink: Optional[Callable[[dict], None]] = None,
) -> dict:
    """Constroi e despacha os alertas do evento.

    Todos os eventos vao ao SIEM; apenas eventos P1 vao ao PagerDuty. Quando um
    sink e `None`, o payload correspondente e apenas construido e devolvido
    (util em testes). Retorna um dicionario com as chaves `siem` e `pagerduty`
    (esta ultima `None` para nao-P1).
    """

    is_p1 = event.priority() is Priority.P1

    with TRACER.start_as_current_span("alerting.dispatch") as span:
        # Contagem de sinks acionados: SIEM sempre; PagerDuty apenas P1.
        span.set_attribute("nexum.sink.siem", 1)
        span.set_attribute("nexum.sink.pagerduty", 1 if is_p1 else 0)
        span.set_attribute("nexum.event_type", event.type)
        span.set_attribute("nexum.priority", event.priority().value)

        siem_record = map_to_siem(event)
        if siem_sink is not None:
            siem_sink(siem_record)

        pagerduty_record: Optional[dict] = None
        if is_p1:
            pagerduty_record = map_to_pagerduty(event)
            if pagerduty_sink is not None:
                pagerduty_sink(pagerduty_record)

        return {"siem": siem_record, "pagerduty": pagerduty_record}
