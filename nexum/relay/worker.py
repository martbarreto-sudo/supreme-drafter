"""Worker Relay do padrao Transactional Outbox do NEXUM.

Este worker drena a tabela `transactional_outbox` (Postgres) usando
`SELECT ... FOR UPDATE SKIP LOCKED` para garantir que multiplos relays possam
rodar em paralelo sem competir pela mesma linha. Cada payload (um CloudEvent
JSON ja serializado) e publicado no Pub/Sub e a linha e marcada como publicada
dentro da mesma transacao, garantindo entrega *at-least-once*.

Falhas de publicacao sao isoladas POR LINHA: uma linha "envenenada" (payload
que sempre falha) nao derruba o lote nem bloqueia a cabeca da fila. Cada falha
incrementa `attempts` e registra `last_error`; ao atingir `max_attempts` a
linha e movida para a DLQ (`dead_lettered_at`), saindo da drenagem ate um
replay autorizado (nexum/relay/replay.py).

Nenhum cliente real (psycopg / google-cloud-pubsub) e importado no topo do
modulo: o worker opera sobre abstracoes DB-API e sobre o `Publisher` Protocol,
o que o torna importavel e testavel sem dependencias externas.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from opentelemetry.trace import Status, StatusCode

from nexum.observability.tracing import TRACER

logger = logging.getLogger("nexum.relay")

# Maximo de tentativas de publicacao antes de dead-letter (env: NEXUM_MAX_ATTEMPTS).
DEFAULT_MAX_ATTEMPTS = 5

# Query central do drenador. FOR UPDATE SKIP LOCKED permite concorrencia segura
# entre multiplas instancias do relay sem bloqueio mutuo. Linhas na DLQ
# (dead_lettered_at NOT NULL) ficam fora da drenagem.
SELECT_BATCH_SQL = (
    "SELECT id, payload, attempts FROM transactional_outbox "
    "WHERE published_at IS NULL AND dead_lettered_at IS NULL "
    "ORDER BY created_at "
    "FOR UPDATE SKIP LOCKED LIMIT %s"
)

MARK_PUBLISHED_SQL = (
    "UPDATE transactional_outbox SET published_at = %s WHERE id = %s"
)

# Registra uma falha de publicacao; quando attempts + 1 atinge o limite, a
# propria UPDATE faz o dead-letter (decisao atomica no banco).
RECORD_FAILURE_SQL = (
    "UPDATE transactional_outbox "
    "SET attempts = attempts + 1, last_error = %s, "
    "dead_lettered_at = CASE WHEN attempts + 1 >= %s THEN %s "
    "ELSE dead_lettered_at END "
    "WHERE id = %s"
)


class Publisher(Protocol):
    """Contrato minimo de um publicador Pub/Sub."""

    def publish(self, topic: str, data: bytes) -> str:
        """Publica `data` no `topic` e retorna o message id."""
        ...


def _to_bytes(payload: Any) -> bytes:
    """Normaliza o payload da outbox para bytes UTF-8.

    Aceita `bytes`, `str` ou estruturas JSON-serializaveis (dict/list).
    """

    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, str):
        return payload.encode("utf-8")
    import json

    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _annotate_publish_span(span: Any, topic: str, payload: Any) -> None:
    """Anota o span `relay.publish` com atributos de mensageria e forenses.

    Le `type`/`correlationid`/`idempotencykey` do payload JSON quando possivel;
    falhas de parse sao silenciosas (o span nao deve interferir na drenagem).
    Sob o provider no-op os `set_attribute` sao no-ops.
    """

    span.set_attribute("messaging.system", "gcp_pubsub")
    span.set_attribute("messaging.destination", topic)
    try:
        import json

        obj: Any = payload
        if isinstance(obj, (bytes, bytearray, str)):
            obj = json.loads(obj)
        if isinstance(obj, dict):
            if obj.get("type") is not None:
                span.set_attribute("nexum.event_type", str(obj["type"]))
            if obj.get("correlationid") is not None:
                span.set_attribute("nexum.correlation_id", str(obj["correlationid"]))
            if obj.get("idempotencykey") is not None:
                span.set_attribute(
                    "nexum.idempotency_key", str(obj["idempotencykey"])
                )
    except Exception:  # noqa: BLE001 - anotacao best-effort, nunca falha a drenagem
        pass


def drain_once(
    conn: Any,
    publisher: Publisher,
    topic: str,
    batch_size: int = 100,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> int:
    """Drena um lote da outbox e publica no Pub/Sub.

    Abre uma transacao, seleciona ate `batch_size` linhas nao publicadas (e
    fora da DLQ) com `FOR UPDATE SKIP LOCKED`, publica cada payload e marca a
    linha como publicada (`published_at = now()`).

    Falha de publicacao NAO derruba o lote: a linha faltosa recebe
    `attempts + 1` / `last_error` (e `dead_lettered_at` ao atingir
    `max_attempts`) e o restante do lote segue. Falha de banco (UPDATE/commit)
    faz rollback de tudo, preservando as linhas nao publicadas
    (at-least-once; o consumidor absorve republicacoes via dedup).
    Retorna a quantidade de eventos publicados.
    """

    cur = conn.cursor()
    published = 0
    try:
        cur.execute(SELECT_BATCH_SQL, (batch_size,))
        rows = cur.fetchall()
        with TRACER.start_as_current_span("relay.drain_once") as batch_span:
            batch_span.set_attribute("messaging.batch.count", len(rows))
            for row in rows:
                row_id, payload, attempts = row[0], row[1], row[2]
                with TRACER.start_as_current_span("relay.publish") as span:
                    _annotate_publish_span(span, topic, payload)
                    try:
                        publisher.publish(topic, _to_bytes(payload))
                    except Exception as exc:  # noqa: BLE001 - isola a linha faltosa
                        span.record_exception(exc)
                        span.set_status(Status(StatusCode.ERROR, str(exc)))
                        now = datetime.now(timezone.utc)
                        cur.execute(
                            RECORD_FAILURE_SQL,
                            (
                                f"{type(exc).__name__}: {exc}",
                                max_attempts,
                                now,
                                row_id,
                            ),
                        )
                        if attempts + 1 >= max_attempts:
                            logger.error(
                                "Outbox id=%s dead-lettered apos %s tentativas: %s",
                                row_id,
                                attempts + 1,
                                exc,
                            )
                        else:
                            logger.warning(
                                "Falha de publicacao outbox id=%s "
                                "(tentativa %s/%s): %s",
                                row_id,
                                attempts + 1,
                                max_attempts,
                                exc,
                            )
                        continue
                    cur.execute(
                        MARK_PUBLISHED_SQL,
                        (datetime.now(timezone.utc), row_id),
                    )
                    published += 1
        conn.commit()
        return published
    except Exception:
        # Falha de banco (SELECT/UPDATE/commit): desfaz tudo para preservar as
        # linhas como nao publicadas (at-least-once).
        conn.rollback()
        raise
    finally:
        close = getattr(cur, "close", None)
        if callable(close):
            close()


def run_forever(
    conn_factory: Callable[[], Any],
    publisher: Publisher,
    topic: str,
    poll_interval: float = 1.0,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> None:
    """Laco principal do relay: drena continuamente e dorme quando vazio.

    `conn_factory` deve retornar uma conexao DB-API pronta para uso. Quando um
    ciclo de `drain_once` nao publica nada, o laco dorme `poll_interval`
    segundos antes de tentar novamente.
    """

    conn = conn_factory()
    while True:
        try:
            count = drain_once(conn, publisher, topic, max_attempts=max_attempts)
        except Exception:
            # Reconstroi a conexao em caso de erro transitorio de I/O.
            conn = conn_factory()
            time.sleep(poll_interval)
            continue
        if count == 0:
            time.sleep(poll_interval)


def _build_pg_conn_factory(dsn: str) -> Callable[[], Any]:
    """Cria uma factory de conexoes psycopg (importacao tardia)."""

    import psycopg  # importado apenas quando executado como processo real

    def factory() -> Any:
        return psycopg.connect(dsn)

    return factory


def _build_pubsub_publisher() -> Publisher:
    """Cria um publicador real do Google Cloud Pub/Sub (importacao tardia)."""

    from google.cloud import pubsub_v1  # type: ignore

    client = pubsub_v1.PublisherClient()

    class _GcpPublisher:
        def publish(self, topic: str, data: bytes) -> str:
            future = client.publish(topic, data)
            return future.result()

    return _GcpPublisher()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NEXUM Worker Relay (Outbox)")
    parser.add_argument(
        "--dsn",
        default=os.environ.get("NEXUM_OUTBOX_DSN", ""),
        help="DSN Postgres (env: NEXUM_OUTBOX_DSN)",
    )
    parser.add_argument(
        "--topic",
        default=os.environ.get("NEXUM_PUBSUB_TOPIC", ""),
        help="Topico Pub/Sub (env: NEXUM_PUBSUB_TOPIC)",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=float(os.environ.get("NEXUM_POLL_INTERVAL", "1.0")),
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=int(
            os.environ.get("NEXUM_MAX_ATTEMPTS", str(DEFAULT_MAX_ATTEMPTS))
        ),
        help="Tentativas de publicacao antes de dead-letter "
        "(env: NEXUM_MAX_ATTEMPTS)",
    )
    args = parser.parse_args()

    conn_factory = _build_pg_conn_factory(args.dsn)
    publisher = _build_pubsub_publisher()
    run_forever(
        conn_factory,
        publisher,
        args.topic,
        args.poll_interval,
        max_attempts=args.max_attempts,
    )
