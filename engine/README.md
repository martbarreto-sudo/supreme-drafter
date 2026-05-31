# Nexum Engine — MVP (Fase 3)

Engine determinístico do Nexum by Tigre. Sem LLM nesta fase — pipeline ponta-a-ponta com Jinja2 e validação HALT / Dado Líquido. Integração com Claude API entra na Fase 4.

## Setup

```bash
cd engine
uv sync --extra dev
uv run pytest -v
uv run uvicorn nexum.api:app --reload
```

## Endpoints

- `GET /healthz` — liveness
- `GET /casos/{feito_id}/vulnerabilidades` — retorna tabela do feito (404 se não catalogado)
- `POST /draft` — gera minuta determinística (Jinja2)
  - Payload: `{ feito_id, peca_tipo, fatos[] }`
  - Retorna **422 + HaltResponse** se algum fato dispositivo não tiver Dado Líquido
  - Retorna **200 + Minuta** caso todos os fatos dispositivos estejam LIQUIDO

## Exemplo de uso

```bash
# HALT — fato sem fonte
curl -X POST localhost:8000/draft -H 'Content-Type: application/json' -d '{
  "feito_id": "Feito-HBM",
  "peca_tipo": "HC",
  "fatos": [{"id": "f1", "proposto": "X aconteceu"}]
}'
# 422 — Módulo 11 acionado

# OK — fato com Dado Líquido
curl -X POST localhost:8000/draft -H 'Content-Type: application/json' -d '{
  "feito_id": "Feito-HBM",
  "peca_tipo": "HC",
  "fatos": [{
    "id": "f1",
    "proposto": "Reconhecimento por foto",
    "verificado": "Reconhecimento por foto isolada, sem fila",
    "fonte": {"uri": "certidao://feito-hbm/fls-12"}
  }]
}'
# 200 — minuta com tabela de vulnerabilidades
```

## Próximos passos (Fase 4)

- Cliente `anthropic` SDK (Claude Sonnet 4.6 + prompt caching no system prompt)
- Caso-piloto Feito-HBM com Temperatura Zero (`temperature=0`)
- Asserções automáticas pós-geração: presença de distinguishing Tema 1.258, citação HC 598.887/SC, tabela preenchida
