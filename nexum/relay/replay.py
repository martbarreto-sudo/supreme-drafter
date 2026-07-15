"""Replay autorizado da DLQ da Transactional Outbox do NEXUM.

Re-enfileira linhas dead-lettered (`dead_lettered_at NOT NULL`) para nova
drenagem pelo relay: zera `attempts`/`last_error`/`dead_lettered_at` e marca o
payload com `isreplay=true`, como manda a extension attribute forense.

Na MESMA transacao, um CloudEvent `br.nexum.infra.replay.executed.v1` (P3) e
inserido na propria outbox como trilha de auditoria — o registro do replay
percorre o mesmo pipeline que os demais eventos forenses, com `operatorid`
identificando quem autorizou.

Como o restante do relay, o modulo opera sobre abstracoes DB-API: nenhum
cliente real e importado no topo.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from nexum.cloudevents import CloudEvent, build_idempotency_key

REPLAY_EXECUTED_TYPE = "br.nexum.infra.replay.executed.v1"
REPLAY_SOURCE = "urn:nexum:platform:dlq-manager"

SELECT_DEAD_SQL = (
    "SELECT id, payload FROM transactional_outbox "
    "WHERE dead_lettered_at IS NOT NULL "
    "ORDER BY created_at "
    "FOR UPDATE SKIP LOCKED LIMIT %s"
)

REQUEUE_SQL = (
    "UPDATE transactional_outbox "
    "SET dead_lettered_at = NULL, attempts = 0, last_error = NULL, "
    "payload = %s "
    "WHERE id = %s"
)

INSERT_AUDIT_SQL = (
    "INSERT INTO transactional_outbox (aggregate_id, event_type, payload) "
    "VALUES (%s, %s, %s)"
)


def _as_dict(payload: Any) -> dict:
    """Normaliza o payload da outbox (JSONB) para dict.

    psycopg devolve JSONB como dict; fakes/testes podem entregar str/bytes.
    """

    if isinstance(payload, dict):
        return payload
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    return json.loads(payload)


def build_replay_audit_event(
    replayed_row_ids: list[int],
    operator_id: str,
    justification: str,
) -> CloudEvent:
    """Constroi o CloudEvent de auditoria do replay (catalogo P3)."""

    execution_id = str(uuid.uuid4())
    subject = f"dlq_{execution_id}"
    return CloudEvent(
        id=str(uuid.uuid4()),
        source=REPLAY_SOURCE,
        type=REPLAY_EXECUTED_TYPE,
        subject=subject,
        time=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        correlationid=str(uuid.uuid4()),
        idempotencykey=build_idempotency_key(subject, "REPLAY_EXECUTED"),
        isreplay=True,
        operatorid=operator_id,
        data={
            "replayed_row_ids": replayed_row_ids,
            "count": len(replayed_row_ids),
            "justification": justification,
        },
    )


def replay_dead_letters(
    conn: Any,
    operator_id: str,
    justification: str = "Replay autorizado da DLQ.",
    limit: int = 100,
) -> int:
    """Re-enfileira ate `limit` linhas da DLQ e audita a execucao.

    Cada linha volta a ser elegivel para drenagem (`dead_lettered_at = NULL`,
    `attempts = 0`) com o payload marcado `isreplay=true`. Se ao menos uma
    linha foi re-enfileirada, o evento de auditoria
    `br.nexum.infra.replay.executed.v1` e inserido na outbox NA MESMA
    transacao. Retorna a quantidade de linhas re-enfileiradas.
    """

    cur = conn.cursor()
    try:
        cur.execute(SELECT_DEAD_SQL, (limit,))
        rows = cur.fetchall()
        replayed_ids: list[int] = []
        for row in rows:
            row_id, payload = row[0], row[1]
            event_dict = _as_dict(payload)
            event_dict["isreplay"] = True
            cur.execute(
                REQUEUE_SQL,
                (json.dumps(event_dict, ensure_ascii=False), row_id),
            )
            replayed_ids.append(row_id)

        if replayed_ids:
            audit = build_replay_audit_event(
                replayed_ids, operator_id, justification
            )
            cur.execute(
                INSERT_AUDIT_SQL,
                (
                    audit.subject,
                    audit.type,
                    json.dumps(audit.model_dump(), ensure_ascii=False),
                ),
            )
        conn.commit()
        return len(replayed_ids)
    except Exception:
        # Replay e tudo-ou-nada: qualquer falha preserva a DLQ intacta.
        conn.rollback()
        raise
    finally:
        close = getattr(cur, "close", None)
        if callable(close):
            close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="NEXUM DLQ Replay (reprocessamento autorizado)"
    )
    parser.add_argument(
        "--dsn",
        default=os.environ.get("NEXUM_OUTBOX_DSN", ""),
        help="DSN Postgres (env: NEXUM_OUTBOX_DSN)",
    )
    parser.add_argument(
        "--operator",
        required=True,
        help="Matricula do analista que autorizou o replay (operatorid)",
    )
    parser.add_argument(
        "--justification",
        default="Replay autorizado da DLQ.",
        help="Justificativa registrada no evento de auditoria",
    )
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    import psycopg  # importado apenas quando executado como processo real

    with psycopg.connect(args.dsn) as conn:
        count = replay_dead_letters(
            conn,
            operator_id=args.operator,
            justification=args.justification,
            limit=args.limit,
        )
    print(f"Replayed {count} dead-lettered event(s).")
