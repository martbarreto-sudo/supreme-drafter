# Nexum Engine — MVP (Fases 3 + 4)

Engine do Nexum by Tigre. Dois caminhos de geração:

- **`/draft`** — determinístico via Jinja2; sem LLM, sem custo de token. Para validar pipeline e HALT.
- **`/draft/llm`** — chama Claude API com adaptive thinking + prompt caching da doutrina. Requer `ANTHROPIC_API_KEY`.

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

## Configuração (Fase 4)

- `ANTHROPIC_API_KEY` — obrigatório para `/draft/llm`. Sem isto, o endpoint retorna 503.
- `NEXUM_MODEL` — opcional. Default: `claude-opus-4-8`. Alternativa: `claude-sonnet-4-6` (custo ~40% menor, qualidade ainda alta).

A engine usa:
- **Adaptive thinking** (`thinking={"type": "adaptive"}`) — Claude decide profundidade do raciocínio
- **Effort `high`** — recomendado para trabalho jurídico sensível
- **Prompt caching** no system prompt (doutrina + protocolo) — reduz custo em ~90% após primeira chamada

> **Nota sobre "Temperatura Zero":** Opus 4.8/4.7 removeram o parâmetro `temperature`. O determinismo do dispositivo é alcançado via prompt rígido + estrutura, não por temperature=0. A metáfora do protocolo permanece válida; a implementação muda.

## Caso-piloto: Feito-HBM (Tema 1.258/STF)

A função `validar_feito_hbm()` audita pós-geração:
- ✅ Distinguishing explícito contra Tema 1.258/STF
- ✅ Citação ao precedente HC 598.887/SC (STJ)
- ✅ Tabela de vulnerabilidades presente

Testes usam `unittest.mock` no cliente Anthropic — zero custo de token em CI.
