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
- `NEXUM_TOKEN` — bearer obrigatório para `/autos` (e recomendado para `/draft/llm` em deploy).
- `CASO_DATA_DIR` — diretório fora do repo onde `/autos` persiste binários e onde os dados reais dos feitos vivem em produção.

## Upload de autos (Dado Líquido por hash)

`POST /autos` recebe um PDF, calcula SHA-256, persiste em `$CASO_DATA_DIR/{feito_id}/{sha256}.pdf` e devolve um `fonte_uri` no esquema `hash://{feito_id}/{sha256}` que é aceito como fonte primária pelo Dado Líquido — ou seja, o upload **ancora** o fato auditável diretamente no protocolo, sem texto colado.

```bash
curl -X POST localhost:8000/autos \
  -H "Authorization: Bearer $NEXUM_TOKEN" \
  -F "feito_id=Feito-HBM" \
  -F "arquivo=@inquerito-fls-12.pdf"
# → { "feito_id": "...", "sha256": "...", "fonte_uri": "hash://Feito-HBM/...", "bytes": "..." }
```

Códigos: `200` ok · `400` feito_id inválido · `401` sem auth · `403` token errado · `413` >20 MiB · `415` não-PDF · `503` env ausente.

A engine usa:
- **Adaptive thinking** (`thinking={"type": "adaptive"}`) — Claude decide profundidade do raciocínio
- **Effort `high`** — recomendado para trabalho jurídico sensível
- **Prompt caching** no system prompt (doutrina + protocolo) — reduz custo em ~90% após primeira chamada

> **Nota sobre "Temperatura Zero":** Opus 4.8/4.7 removeram o parâmetro `temperature`. O determinismo do dispositivo é alcançado via prompt rígido + estrutura, não por temperature=0. A metáfora do protocolo permanece válida; a implementação muda.

## Quality Gates (quality_score)

`/draft/llm` roda `avaliar_qualidade()` pós-geração e devolve um `quality.score` (0-100) com o detalhe de cada gate. Cinco gates determinísticos auditam traços epistemológicos do protocolo:

| Gate | Verifica |
|---|---|
| `fonte_por_fato` | Cada fato dispositivo tem sua fonte primária citada na peça |
| `precedente_do_eixo` | Os precedentes/temas do eixo dogmático aparecem na minuta |
| `auditoria_silencio` | Bloco de Auditoria de Silêncio presente |
| `pedido_presente` | Há pedido/requerimento |
| `assinatura_tigre` | Ausência de submissão burocrática (data venia, ousamos…) |

Isto generaliza o `validar_feito_hbm` para qualquer feito e dá ao operador um sinal de qualidade verificável antes da assinatura — não substitui a revisão humana do advogado-operador.

## Caso-piloto: Feito-HBM (Tema 1.258/STF)

A função `validar_feito_hbm()` audita pós-geração:
- ✅ Distinguishing explícito contra Tema 1.258/STF
- ✅ Citação ao precedente HC 598.887/SC (STJ)
- ✅ Tabela de vulnerabilidades presente

Testes usam `unittest.mock` no cliente Anthropic — zero custo de token em CI.
