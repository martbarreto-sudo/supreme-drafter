# Chart Helm — NEXUM (consumidor + relay)

Orquestra o pipeline forense NEXUM Tier 0 no Kubernetes: o **consumidor**
(FastAPI/uvicorn, `nexum.consumer.asgi:app`) e o **relay** Outbox
(`python -m nexum.relay.worker`). Espelha o contrato de env do
[`docker-compose.yml`](../../../docker-compose.yml) e injeta configuracao
OpenTelemetry.

## Servicos externos (premissa)

Postgres, Redis e Pub/Sub sao tratados como **externos** — o chart NAO os
provisiona (nem via subchart), o que o mantem renderizavel offline. Configure
os endpoints em `externalServices`:

| Componente | Env injetada     | Valor (values)                        |
|------------|------------------|---------------------------------------|
| relay      | `NEXUM_OUTBOX_DSN`      | `externalServices.postgres.dsn`  |
| relay      | `NEXUM_PUBSUB_TOPIC`    | `externalServices.pubsub.topic`  |
| relay      | `PUBSUB_EMULATOR_HOST`  | `externalServices.pubsub.emulatorHost` (so se != "") |
| relay      | `NEXUM_POLL_INTERVAL` / `NEXUM_MAX_ATTEMPTS` | `relay.pollInterval` / `relay.maxAttempts` |
| consumidor | `REDIS_URL`            | `externalServices.redis.url`     |

> Para adicionar Postgres/Redis dentro do cluster no futuro, veja o comentario
> em `Chart.yaml` (subcharts Bitnami).

## Injecao OpenTelemetry

Quando `otel.enabled=true`, ambos os deployments recebem:

- `OTEL_TRACES_EXPORTER` = `otel.exporter` (default `otlp`)
- `OTEL_EXPORTER_OTLP_ENDPOINT` = `otel.endpoint`
- `OTEL_SERVICE_NAME` = `<otel.serviceNamePrefix>-consumer` / `-relay`
- `OTEL_RESOURCE_ATTRIBUTES` (namespace + service.name)

`nexum/observability/tracing.py` le `OTEL_TRACES_EXPORTER` e
`OTEL_EXPORTER_OTLP_ENDPOINT` (no-op por padrao quando nenhum collector existe).

## Secrets (producao)

DSN/URL sao sensiveis. Em producao, crie um Secret com as chaves `outbox-dsn` e
`redis-url` e aponte `secrets.existingSecret` para ele — os deployments passam a
ler as envs via `secretKeyRef`. Um Secret de exemplo (opt-in, apenas dev) pode
ser gerado com `secrets.create=true`.

## Escala

- **consumidor**: `consumer.replicaCount` (default 2) ou HPA
  (`consumer.autoscaling.enabled=true`). Idempotente via Redis (`SET NX`).
- **relay**: `relay.replicaCount` (default 1). O drenador usa
  `SELECT ... FOR UPDATE SKIP LOCKED`, entao **e seguro escalar >1** — multiplas
  instancias nao competem pela mesma linha da outbox.

## Validar (render, sem cluster)

```bash
helm lint deploy/helm/nexum
helm template nexum deploy/helm/nexum > /tmp/rendered.yaml
helm template nexum deploy/helm/nexum -f deploy/helm/nexum/values-dev.yaml > /tmp/rendered-dev.yaml
python3 -c "import yaml; list(yaml.safe_load_all(open('/tmp/rendered.yaml'))); print('RENDER_OK')"
```

## Instalar

```bash
helm install nexum deploy/helm/nexum -f values.yaml
# variante dev (nomes de servico do compose + emulador Pub/Sub):
helm install nexum deploy/helm/nexum -f deploy/helm/nexum/values-dev.yaml
```
