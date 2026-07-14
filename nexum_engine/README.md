# NEXUM Engine v5.5 — fundação de contratos e adaptadores

Arquitetura hexagonal mínima da engine. **Nada aqui lê credencial ou abre
conexão**: os contratos vivem em `ports.py`, as implementações em
`adapters/`, e as dependências reais entram por injeção no gatilho HITL.

## Camadas

| Módulo | Papel |
|---|---|
| `ports.py` | Protocols (`DatabasePort`, `EmbedderPort`, `CompletionPort`) — a engine depende só disto |
| `models.py` | Cânone único de model IDs + `validar_modelo()` (bloqueio de regressão em runtime) |
| `adapters/asyncpg_adapter.py` | `AsyncpgAdapter` — PostgreSQL/Supabase sobre `asyncpg.Pool` injetado |
| `adapters/vertex_embed_adapter.py` | `VertexEmbedAdapter` — embeddings sobre cliente Vertex injetado |
| `adapters/anthropic_adapters.py` | `AnthropicVertexAdapter` (consolidador, Opus 4.8) e `DirectAPIAdapter` (agentes paralelos, Sonnet 4.6) |
| `tests/` | Suíte isolada (fakes; zero credenciais) + `TestModelStringRegression` |

## Cânone de modelos

- Agentes paralelos (níveis 1-2): `claude-sonnet-4-6`
- Consolidador de peer-review (nível 4): `claude-opus-4-8`
- **Proibidos** (aposentados; o CI quebra se reaparecerem): o antigo
  Sonnet 3.5 datado e demais IDs em `models.MODELOS_PROIBIDOS`.
- Vertex AI: modelos de geração atual usam o **ID puro**; o formato
  `nome@data` só se aplica a snapshots datados (`modelo_para_vertex`).

## Gatilho HITL — o que o operador injeta para o deploy

```python
import asyncpg
from anthropic import AsyncAnthropic, AsyncAnthropicVertex

from nexum_engine.adapters import (
    AnthropicVertexAdapter, AsyncpgAdapter, DirectAPIAdapter,
)
from nexum_engine.models import REGIAO_VERTEX

# 1. PostgreSQL/Supabase (consultas isoladas por Row-Level Security)
db = AsyncpgAdapter(await asyncpg.create_pool(dsn=SUPABASE_DSN))

# 2. Consolidador via Vertex (autenticação ADC do GCP)
consolidador = AnthropicVertexAdapter(
    AsyncAnthropicVertex(project_id=GCP_PROJECT, region=REGIAO_VERTEX)
)

# 3. Agentes paralelos via API direta (ANTHROPIC_API_KEY)
agente = DirectAPIAdapter(AsyncAnthropic())
```

Sem a injeção, qualquer chamada falha com um erro que aponta o passo
pendente (`*NaoInjetadoError`) — nunca com falha silenciosa.

## Testes

```bash
pytest -q nexum_engine/   # 31 testes; sem rede, sem credenciais
```

CI: `.github/workflows/nexum-engine-tests.yml` roda a suíte em todo
push/PR que toque `nexum_engine/**`. O gate de peer-review dual-provider
(`peer-review.yml`) já observa `nexum_engine/**` desde o commit `817afbc`.
