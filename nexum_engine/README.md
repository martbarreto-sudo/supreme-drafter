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
| `verdade/` | **Loop de verdade**: `Precedente`, `FonteDePrecedentes` (JSON local-first e Supabase) e `auditar_citacoes()` — o portão `zero_tolerance` do auditor |
| `schema/precedentes.sql` | DDL do Supabase (`precedentes_verificados`): quarentena, CHECKs de fonte, RLS leitura-só-citável, GIN em tags, pgvector reservado p/ fase 2 |
| `verdade/exportar_sql.py` | Carga MINDJUS → SQL: manifesto idempotente de INSERTs (dedupe por número normalizado, órfãos sem fonte entram quarentenados) |
| `verdade/gate.py` | Gate de citações (CLI): postura binária p/ CI — bloqueado (exit 1) se citação fora da base; INCONCLUSIVO opcional sem base |
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

## Loop de verdade (auditoria de citações)

```python
from nexum_engine.verdade import FonteJsonVerificada, auditar_citacoes

# Local-first: aponta para a base MINDJUS verificada (warroom-tigre)
fonte = FonteJsonVerificada("caminho/para/mindjus_data")
relatorio = await auditar_citacoes(texto_da_minuta, fonte)
relatorio.veredito          # "PROTOCOLAVEL" | "NAO_PROTOCOLAVEL"
relatorio.nao_verificadas   # citações bloqueantes (zero_tolerance)
```

Regras invioláveis das fontes: precedente **em quarentena**
(`verificacao_pendente`) ou **sem fonte de verificação** nunca é retornado —
nem no JSON, nem no SQL (filtro na própria query + RLS no banco). Para o
Supabase, troque por `FonteSupabase(AsyncpgAdapter(pool))` após aplicar
`schema/precedentes.sql`.

Para povoar o banco (passo do operador, uma vez):

```bash
python -m nexum_engine.verdade.exportar_sql caminho/para/mindjus_data -o seed.sql
# revisar o seed.sql e executá-lo como OWNER/service role no SQL Editor
# (a RLS nega escrita aos papéis da engine de propósito)
```

O manifesto é determinístico e idempotente; registros legítimos sem
`fonte_verificacao` entram JÁ EM QUARENTENA com motivo automático — nunca
quebram os CHECKs nem viram citáveis por acidente.

## Testes

```bash
pytest -q nexum_engine/   # 64 testes; sem rede, sem credenciais
```

CI: `.github/workflows/nexum-engine-tests.yml` roda a suíte em todo
push/PR que toque `nexum_engine/**`. O gate de peer-review dual-provider
(`peer-review.yml`) já observa `nexum_engine/**` desde o commit `817afbc`.

O **gate de citações** (`.github/workflows/citation-gate.yml`) audita
peças/minutas em texto (`pecas/**`, `minutas/**`) contra a base MINDJUS a
cada PR: com o secret `WARROOM_TIGRE_TOKEN` (PAT fine-grained, Contents:
Read no warroom-tigre) ele clona a base e aplica a postura binária; sem o
token, sela ⚪ INCONCLUSIVO — nunca reprova o que não pôde auditar.
