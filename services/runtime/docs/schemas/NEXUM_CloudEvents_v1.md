# Especificacao NEXUM CloudEvents v1.0

Contrato de eventos do pipeline forense NEXUM TIER 0. Baseado na especificacao
**CloudEvents v1.0 (CNCF)**, com quatro *extension attributes* forenses
proprietarias. Todo evento trafega em modo estruturado (JSON) da outbox
transacional ate o consumidor idempotente.

## 1. Envelope CloudEvents

| Campo             | Obrigatorio | Tipo   | Descricao                                                        |
|-------------------|:-----------:|--------|------------------------------------------------------------------|
| `specversion`     | sim         | string | Fixo em `"1.0"`.                                                  |
| `id`              | sim         | string | Identificador unico do evento (UUID).                            |
| `source`          | sim         | string | URN da origem, ex.: `urn:nexum:artifact-pipeline:scanner`.       |
| `type`            | sim         | string | Tipo do evento (ver catalogo), ex.: `br.nexum.artifact.quarantined.v1`. |
| `subject`         | sim         | string | Recurso alvo — o `artifact_id`.                                  |
| `time`            | sim         | string | Timestamp RFC 3339 (UTC).                                        |
| `datacontenttype` | sim         | string | Fixo em `application/json`.                                      |
| `data`            | sim         | object | Payload especifico do evento.                                    |

## 2. Extension Attributes Forenses

Segundo a especificacao CloudEvents, os **nomes** de extension attributes devem
conter apenas caracteres **alfanumericos minusculos** (`[a-z0-9]`) — sem
underscores nem hifens. O modelo `CloudEvent` valida essa regra em tempo de
importacao.

| Atributo         | Tipo   | Default    | Descricao                                                     |
|------------------|--------|------------|---------------------------------------------------------------|
| `correlationid`  | string | —          | UUID da saga; correlaciona todos os eventos de um mesmo fluxo.|
| `idempotencykey` | string | —          | Chave composta `artifact_id:target_state`.                    |
| `isreplay`       | bool   | `false`    | `true` quando o evento e reprocessado a partir da DLQ.        |
| `operatorid`     | string | `"system"` | Matricula do analista responsavel, ou `system`.               |

## 3. Catalogo de Eventos

| Tipo                                    | Cenario                                                      | Prioridade | Exemplo |
|-----------------------------------------|--------------------------------------------------------------|:----------:|---------|
| `br.nexum.artifact.quarantined.v1`      | Artefato isolado apos deteccao positiva de malware na esteira.| **P2**    | [artifact_quarantined.json](../../nexum/schemas/artifact_quarantined.json) |
| `br.nexum.artifact.integrity.alert.v1`  | Divergencia de hash criptografico pos-upload.                | **P1**     | [integrity_alert.json](../../nexum/schemas/integrity_alert.json) |
| `br.nexum.artifact.compensate.v1`       | Compensacao de saga apos esgotamento de retentativas.        | **P1**     | [compensate_pipeline.json](../../nexum/schemas/compensate_pipeline.json) |
| `br.nexum.infra.replay.executed.v1`     | Reprocessamento de DLQ autorizado por operador.              | **P3**     | [replay_executed.json](../../nexum/schemas/replay_executed.json) |

### Matriz de prioridades

- **P1** — integridade comprometida e compensacao de saga. Roteados a SIEM
  **e** PagerDuty (`severity: critical`).
- **P2** — quarentena. Roteado apenas a SIEM (`event.severity: 5`).
- **P3** — replay de infraestrutura. Roteado apenas a SIEM.
- Tipos nao mapeados assumem **P3** por padrao.

## 4. Garantias de Entrega

| Camada          | Mecanismo                                        | Garantia          |
|-----------------|--------------------------------------------------|-------------------|
| Outbox → Relay  | `SELECT ... FOR UPDATE SKIP LOCKED` + rollback   | at-least-once     |
| Relay → Pub/Sub | `publish` com marcacao transacional              | at-least-once     |
| Pub/Sub → Consumidor | dedup Redis `SET NX` sobre `idempotencykey` | descarta duplicatas |

**Resultado:** `at-least-once no transporte + SETNX no Redis = effectively-once`.

Nenhum evento e perdido (a linha da outbox so e marcada como publicada apos o
`publish`), e nenhuma transicao de estado e processada duas vezes (a
`idempotencykey` bloqueia reentregas no consumidor).
