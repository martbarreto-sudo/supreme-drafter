"""Worker Relay do padrao Transactional Outbox do NEXUM.

Este worker drena a tabela `transactional_outbox` (Postgres) usando
`SELECT ... FOR UPDATE SKIP LOCKED` para garantir que multiplos relays possam
rodar em paralelo sem competir pela mesma linha. Cada payload (um CloudEvent
JSON ja serializado) e publicado no Pub/Sub e a linha e marcada como publicada
dentro da mesma transacao, garantindo entrega *at-least-once*.

Nenhum cliente real (psycopg / google-cloud-pubsub) e importado no topo do
modulo: o worker opera sobre abstracoes DB-API e sobre o `Publisher` Protocol,
o que o torna importavel e testavel sem dependencias externas.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

# Query central do drenador. FOR UPDATE SKIP LOCKED permite concorrencia segura
# entre multiplas instancias do relay sem bloqueio mutuo.
SELECT_BATCH_SQL = (
    "SELECT id, payload FROM transactional_outbox "
    "WHERE published_at IS NULL ORDER BY created_at "
    "FOR UPDATE SKIP LOCKED LIMIT %s"
)

MARK_PUBLISHED_SQL = (
    "UPDATE transactional_outbox SET published_at = %s WHERE id = %s"
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


def drain_once(
    conn: Any,
    publisher: Publisher,
    topic: str,
    batch_size: int = 100,
) -> int:
    """Drena um lote da outbox e publica no Pub/Sub.

    Abre uma transacao, seleciona ate `batch_size` linhas nao publicadas com
    `FOR UPDATE SKIP LOCKED`, publica cada payload e marca a linha como
    publicada (`published_at = now()`). Em caso de falha de publicacao, faz
    rollback para que a linha permaneca disponivel numa proxima passada
    (semantica at-least-once). Retorna a quantidade de eventos publicados.
    """

    cur = conn.cursor()
    published = 0
    try:
        cur.execute(SELECT_BATCH_SQL, (batch_size,))
        rows = cur.fetchall()
        for row in rows:
            row_id, payload = row[0], row[1]
            publisher.publish(topic, _to_bytes(payload))
            cur.execute(
                MARK_PUBLISHED_SQL,
                (datetime.now(timezone.utc), row_id),
            )
            published += 1
        conn.commit()
        return published
    except Exception:
        # Falha na publicacao ou na marcacao: desfaz tudo para preservar as
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
) -> None:
    """Laco principal do relay: drena continuamente e dorme quando vazio.

    `conn_factory` deve retornar uma conexao DB-API pronta para uso. Quando um
    ciclo de `drain_once` nao publica nada, o laco dorme `poll_interval`
    segundos antes de tentar novamente.
    """

    conn = conn_factory()
    while True:
        try:
            count = drain_once(conn, publisher, topic)
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
    args = parser.parse_args()

    conn_factory = _build_pg_conn_factory(args.dsn)
    publisher = _build_pubsub_publisher()
    run_forever(conn_factory, publisher, args.topic, args.poll_interval)
