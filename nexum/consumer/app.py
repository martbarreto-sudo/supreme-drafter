"""Consumidor FastAPI idempotente do pipeline forense NEXUM.

Recebe CloudEvents em modo estruturado (JSON no corpo), deduplica via Redis
(`SET NX`) usando a `idempotencykey`, e roteia eventos P1 para o dispatcher de
alertas (SIEM/PagerDuty). A dedup garante semantica *effectively-once* sobre um
transporte at-least-once.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable, Optional, Protocol

from fastapi import FastAPI

from nexum.alerting import dispatcher as default_dispatcher
from nexum.cloudevents import CloudEvent, Priority

logger = logging.getLogger("nexum.consumer")

# TTL da chave de idempotencia: 7 dias (em segundos).
IDEMPOTENCY_TTL_SECONDS = 7 * 24 * 60 * 60
IDEMPOTENCY_PREFIX = "nexum:idem:"


class RedisLike(Protocol):
    """Contrato minimo de um cliente Redis para dedup (SET com NX + EX)."""

    def set(
        self,
        name: str,
        value: Any,
        *,
        nx: bool = False,
        ex: Optional[int] = None,
    ) -> Optional[bool]:
        """Executa SET; com nx=True retorna verdadeiro apenas se criou a chave."""
        ...


def create_app(redis_client: RedisLike, dispatcher: Any) -> FastAPI:
    """Fabrica de aplicacao FastAPI com dependencias injetadas (testavel)."""

    app = FastAPI(title="NEXUM Consumidor Idempotente", version="1.0.0")

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    @app.post("/events")
    def receive_event(event: CloudEvent) -> dict:
        key = f"{IDEMPOTENCY_PREFIX}{event.idempotencykey}"
        created = redis_client.set(
            key, event.id, nx=True, ex=IDEMPOTENCY_TTL_SECONDS
        )
        if not created:
            logger.info(
                "Evento duplicado descartado idempotencykey=%s",
                event.idempotencykey,
            )
            return {
                "status": "duplicate",
                "idempotencykey": event.idempotencykey,
            }

        priority = event.priority()
        logger.info(
            "Evento aceito type=%s priority=%s idempotencykey=%s",
            event.type,
            priority.value,
            event.idempotencykey,
        )
        if priority is Priority.P1:
            dispatcher.dispatch(event)

        return {"status": "accepted"}

    return app


def _default_redis_client() -> RedisLike:
    """Constroi um cliente Redis real a partir de REDIS_URL (importacao tardia)."""

    import redis  # importado apenas na inicializacao do processo real

    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    return redis.Redis.from_url(url, decode_responses=True)


def get_app() -> FastAPI:
    """Ponto de entrada de producao: le env e injeta cliente/dispatcher reais."""

    return create_app(_default_redis_client(), default_dispatcher)
