# NEXUM TIER 0 — Pipeline Forense de Eventos (CloudEvents v1.0)

Pipeline de evidencias forenses do NEXUM baseado em **CloudEvents v1.0 (CNCF)**.
Garante rastreabilidade ponta-a-ponta e roteamento de incidentes criticos para
SIEM e PagerDuty, com semantica *effectively-once*.

## Arquitetura

```
  Transactional Outbox (Postgres)
        │  SELECT ... FOR UPDATE SKIP LOCKED
        ▼
  Worker Relay (drena a outbox)   ── nexum/relay/worker.py
        │  publish(topic, bytes)
        │      └─ falha N× ──► DLQ (dead_lettered_at)
        │                        └─ replay autorizado ── nexum/relay/replay.py
        ▼
  Pub/Sub (transporte at-least-once)
        │
        ▼
  Consumidor Idempotente (FastAPI) ── nexum/consumer/app.py
        │  SET NX  (dedup Redis; DEL + 500 se dispatch falhar)
        ▼
  Dispatcher de Alertas (P1)       ── nexum/alerting/dispatcher.py
        ├── SIEM (ECS)      todos os eventos
        └── PagerDuty (v2)  apenas P1
```

1. **Transactional Outbox** — cada mutacao de dominio grava, na mesma transacao
   Postgres, uma linha na tabela `transactional_outbox` contendo o CloudEvent
   serializado. Sem publicacao direta no broker: a atomicidade do evento e
   garantida pelo banco.
2. **Worker Relay** — drena a outbox com `SELECT ... FOR UPDATE SKIP LOCKED`,
   permitindo multiplas instancias concorrentes sem disputa de linha. Publica no
   Pub/Sub e marca `published_at` na mesma transacao. Falha de publicacao e
   **isolada por linha**: a linha faltosa acumula `attempts`/`last_error` (e vai
   a DLQ ao atingir `NEXUM_MAX_ATTEMPTS`, padrao 5) sem derrubar o lote nem
   bloquear a cabeca da fila; as demais linhas seguem (**at-least-once**).
3. **Consumidor Idempotente** — API FastAPI (`POST /events`) valida o envelope
   CloudEvent, deduplica via Redis `SET NX` sobre a `idempotencykey` (TTL 7
   dias) e roteia eventos P1 ao dispatcher. Se o dispatch P1 falhar, a chave e
   **liberada** (`DEL`) e a resposta e 500: a redelivery reprocessa o evento em
   vez de descarta-lo como duplicata (nenhum alerta critico se perde).
4. **Dispatcher** — mapeia o evento para um registro SIEM no estilo ECS (todos
   os eventos) e, para P1, um payload da PagerDuty Events API v2.

## Catalogo de Eventos

| Tipo                                    | Cenario                                      | Prioridade | Exemplo |
|-----------------------------------------|----------------------------------------------|:----------:|---------|
| `br.nexum.artifact.quarantined.v1`      | Artefato isolado por deteccao de malware     | **P2**     | [artifact_quarantined.json](schemas/artifact_quarantined.json) |
| `br.nexum.artifact.integrity.alert.v1`  | Divergencia de hash criptografico            | **P1**     | [integrity_alert.json](schemas/integrity_alert.json) |
| `br.nexum.artifact.compensate.v1`       | Compensacao de saga (rollback do pipeline)   | **P1**     | [compensate_pipeline.json](schemas/compensate_pipeline.json) |
| `br.nexum.infra.replay.executed.v1`     | Reprocessamento de DLQ autorizado            | **P3**     | [replay_executed.json](schemas/replay_executed.json) |

## Extension Attributes Forenses

Nomes em *lowercase alphanumeric* (sem underscore/hifen), conforme CloudEvents:

| Atributo         | Tipo   | Descricao                                            |
|------------------|--------|------------------------------------------------------|
| `correlationid`  | string | UUID da saga (correlaciona todos os eventos do fluxo)|
| `idempotencykey` | string | Chave composta `artifact_id:target_state`            |
| `isreplay`       | bool   | Indica reprocessamento a partir da DLQ               |
| `operatorid`     | string | Matricula do analista ou `system`                    |

## Como rodar os testes

```bash
cd nexum
pip install -r requirements.txt
pytest -q
```

Os testes usam apenas *fakes* — nao ha dependencia de rede, Postgres, Redis ou
Pub/Sub. `psycopg` e `google-cloud-pubsub` sao carregados via importacao tardia
apenas quando o relay/consumidor rodam como processos reais.

## Rodar localmente (docker-compose)

Um `docker-compose.yml` na raiz do repositorio sobe o pipeline ponta-a-ponta.
A imagem unica (`nexum/Dockerfile`) roda tanto o consumidor quanto o relay.

```bash
make up      # docker compose up -d --build
make logs    # acompanha os logs de todos os servicos
make down    # derruba tudo e remove volumes (-v)
```

### Servicos e portas

| Servico    | Imagem                                            | Porta host | Papel |
|------------|---------------------------------------------------|:----------:|-------|
| `postgres` | postgres:16-alpine                                | 5432       | Transactional Outbox; carrega `nexum/infra/schema.sql` (DDL + seeds) no boot |
| `redis`    | redis:7-alpine                                    | 6379       | Dedup `SET NX` (idempotencykey) |
| `pubsub`   | cloud-sdk:emulators                               | 8085       | Emulador Google Pub/Sub (`--project=nexum-local`) |
| `consumer` | build `nexum/Dockerfile`                          | 8000       | FastAPI `POST /events` / `GET /healthz` (uvicorn `nexum.consumer.asgi:app`) |
| `relay`    | build `nexum/Dockerfile`                          | —          | `python -m nexum.relay.worker` drenando a outbox |

### Fluxo end-to-end

```
schema.sql (seeds)                            ┌─ SIEM  (todos)
   │ INSERT em transactional_outbox           │
   ▼                                          │
postgres ──SELECT..FOR UPDATE SKIP LOCKED──► relay ──publish──► pubsub (emulador)
                                                                    │
                                                                    ▼
                                              consumer (FastAPI) ──SET NX (redis)──► dispatcher P1 ─┴─ PagerDuty (P1)
```

O relay le `NEXUM_OUTBOX_DSN` e `NEXUM_PUBSUB_TOPIC` do ambiente (definidos no
compose) e publica no emulador via `PUBSUB_EMULATOR_HOST`.

### Testes

```bash
make test              # unitarios (fakes, sem infra): -m "not integration"
make test-integration  # integracao: requer `make up` (senao SKIP)
make psql              # abre psql no container postgres
```

O smoke test (`nexum/infra/smoke_test.py`) e marcado com `@pytest.mark.integration`
e faz `pytest.skip("infra not up")` quando Postgres/Redis nao estao acessiveis,
de modo que `make test` nunca falha por ausencia de infra.

## DLQ e Replay Autorizado

Uma linha cujo payload falha `NEXUM_MAX_ATTEMPTS` vezes seguidas (payload
envenenado, downstream fora) recebe `dead_lettered_at` e **sai da drenagem** —
a fila nunca fica bloqueada por uma linha faltosa. As colunas `attempts` e
`last_error` preservam o diagnostico.

O reprocessamento e uma acao **autorizada e auditada** (`nexum/relay/replay.py`):

```bash
python -m nexum.relay.replay --operator MATRICULA_X --justification "downstream ok"
```

O replay re-enfileira as linhas da DLQ (`attempts = 0`, payload marcado
`isreplay=true`) e, na **mesma transacao**, insere na outbox o evento de
auditoria [`br.nexum.infra.replay.executed.v1`](schemas/replay_executed.json)
(P3) com o `operatorid` de quem autorizou — a trilha do replay percorre o
proprio pipeline.

Inspecao da DLQ via `make psql`:

```sql
SELECT id, event_type, attempts, last_error, dead_lettered_at
  FROM transactional_outbox WHERE dead_lettered_at IS NOT NULL;
```

## Garantia de Entrega

> **at-least-once no transporte + SETNX no Redis = effectively-once**

O relay garante que nenhum evento se perde (falha de banco preserva a linha na
outbox; falha de publicacao acumula tentativas ate a DLQ, de onde so sai por
replay autorizado), podendo, no pior caso, republicar. O consumidor absorve
duplicatas via `SET NX` sobre a `idempotencykey` — e libera a chave quando o
dispatch falha, garantindo que a redelivery reprocesse. O resultado e
processamento **efetivamente unico** de cada transicao de estado, sem perda de
alertas P1.

## Especificacao

Detalhamento do envelope, extensions e catalogo em
[../docs/schemas/NEXUM_CloudEvents_v1.md](../docs/schemas/NEXUM_CloudEvents_v1.md).
