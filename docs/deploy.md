# Deploy — Nexus by Tigre no Railway

Decisão consolidada e procedimento passo-a-passo para colocar o engine no ar.
Plataforma escolhida: **Railway** (justificativa em commits anteriores —
setup mais rápido e barato para founder-solo).

## Arquitetura

```
GitHub push ──▶ GitHub Actions (CI: ruff + pytest 113/113)
                    │
                    └──▶ Railway (build via Dockerfile)
                              │
                              ├──▶ container nexus (FastAPI + uvicorn)
                              │         │
                              │         ├──▶ Postgres (Railway add-on)
                              │         ├──▶ Anthropic API (geração)
                              │         └──▶ Stripe API (billing)
                              │
                              └──▶ volume persistente (CASO_DATA_DIR)
```

## Pré-requisitos do operador (você)

1. Conta no Railway (https://railway.app — login com GitHub)
2. Conta na Anthropic com API key gerada
3. Conta no Stripe + Price IDs criados (Solo / Banca / Corporate) em Dashboard → Products
4. Domínio próprio (opcional para o MVP — Railway dá um `*.up.railway.app`)

## Passo-a-passo Railway (10-15 minutos)

### 1. Criar projeto e conectar repo

- Railway dashboard → **New Project** → **Deploy from GitHub repo**
- Selecionar `martbarreto-sudo/supreme-drafter`
- Railway detecta o `railway.toml` na raiz e usa `engine/Dockerfile` automaticamente

### 2. Provisionar Postgres

- No mesmo projeto: **+ Create** → **Database** → **Add PostgreSQL**
- Railway cria o serviço e expõe `DATABASE_URL` automaticamente para o app
- **Ajuste:** o Postgres do Railway entrega `postgresql://`; nosso código usa
  `postgresql+asyncpg://`. Configure essa env var manualmente no serviço:
  - Vá em **Variables** do serviço nexus
  - `DATABASE_URL = ${{Postgres.DATABASE_URL}}` (referência) **NÃO** funciona direto
  - Use **`DATABASE_URL = postgresql+asyncpg://...`** manualmente, copiando os
    valores de host/user/password/db do serviço Postgres

### 3. Cadastrar secrets (no painel, NUNCA em chat)

No serviço nexus → **Variables** → adicionar uma a uma:

```
ANTHROPIC_API_KEY      sk-ant-...
NEXUS_MODEL            claude-opus-4-8   (opcional; default já é esse)
NEXUS_TOKEN            <gere 32+ chars aleatórios — para endpoints admin>
JWT_SECRET             <gere 32+ chars aleatórios — openssl rand -hex 32>

STRIPE_SECRET_KEY      sk_live_... (teste com sk_test_ primeiro)
STRIPE_WEBHOOK_SECRET  whsec_...   (gerado ao criar webhook no Stripe)
STRIPE_PRICE_SOLO      price_...   (do dashboard Stripe → Products)
STRIPE_PRICE_BANCA     price_...
STRIPE_PRICE_CORPORATE price_...

FRONTEND_URL           https://app.seu-dominio.com  (para success/cancel do checkout)
CORS_ORIGINS           https://app.seu-dominio.com  (comma-separated)
```

Gerar secrets seguros localmente:
```bash
openssl rand -hex 32
```

### 4. Configurar volume persistente para CASO_DATA_DIR

- Railway dashboard → serviço nexus → **Volumes** → **+ New Volume**
- Mount path: `/data/feitos`
- Size: começa com 5 GB; aumenta conforme volume
- O Dockerfile já tem `CASO_DATA_DIR=/data/feitos` como default

### 5. Deploy

- Push para `master` (ou a branch que você decidir como deploy branch)
- Railway dispara build automaticamente
- Acompanhar logs em **Deployments**
- Primeira execução: container faz `alembic upgrade head` antes de subir uvicorn
- Healthcheck `/healthz` precisa responder em 30s pós-boot (configurado em `railway.toml`)

### 6. Configurar webhook do Stripe

- Stripe dashboard → **Developers** → **Webhooks** → **Add endpoint**
- URL: `https://<seu-app>.up.railway.app/billing/webhook`
- Eventos: `checkout.session.completed`, `invoice.payment_succeeded`,
  `invoice.payment_failed`, `customer.subscription.deleted`
- Stripe gera `whsec_...` — copie e configure como `STRIPE_WEBHOOK_SECRET` no Railway
- **Redeploy** para que o serviço pegue o secret

### 7. Smoke test

```bash
APP=https://<seu-app>.up.railway.app

# liveness
curl $APP/healthz
# → {"status":"ok"}

# signup
curl -X POST $APP/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email":"smoke@test.com",
    "name":"Smoke Test",
    "oab_numero":"12345",
    "oab_uf":"PE",
    "password":"senhaForte12345",
    "aceito_tos":true,
    "tos_version":1
  }'

# login
TOKEN=$(curl -X POST $APP/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke@test.com","password":"senhaForte12345"}' | jq -r .access_token)

# subscription (deve mostrar TRIAL com 3 peças)
curl $APP/billing/subscription -H "Authorization: Bearer $TOKEN"
```

## Variáveis de ambiente — referência completa

| Variável | Obrigatória | Default | Comentário |
|---|---|---|---|
| `DATABASE_URL` | sim | — | `postgresql+asyncpg://...` |
| `JWT_SECRET` | sim | — | ≥ 32 chars, rotacionar a cada deploy se possível |
| `JWT_TTL_MINUTES` | não | 15 | Expiração do JWT |
| `ANTHROPIC_API_KEY` | sim | — | Para `/draft/llm` |
| `NEXUS_MODEL` | não | `claude-opus-4-8` | Ou `claude-sonnet-4-6` para reduzir custo |
| `NEXUS_TOKEN` | não | — | Bearer para endpoints admin (futuros) |
| `CASO_DATA_DIR` | não | `/data/feitos` | Onde uploads e minutas vivem |
| `STRIPE_SECRET_KEY` | sim para /billing | — | `sk_live_...` em produção |
| `STRIPE_WEBHOOK_SECRET` | sim para /billing | — | `whsec_...` do dashboard Stripe |
| `STRIPE_PRICE_SOLO` | sim para /billing | — | ID do price recorrente Solo |
| `STRIPE_PRICE_BANCA` | sim para /billing | — | ID do price recorrente Banca |
| `STRIPE_PRICE_CORPORATE` | sim para /billing | — | ID do price recorrente Corporate |
| `FRONTEND_URL` | recomendado | `http://localhost:3000` | Base para success/cancel URLs |
| `CORS_ORIGINS` | recomendado | (vazio) | Comma-separated; sem isto, CORS desligado |
| `NEXUS_RATE_LIMIT_DISABLED` | não | (off) | `=1` desliga rate limit (só testes/debug) |

## Quando algo dá errado

| Sintoma | Causa provável | Fix |
|---|---|---|
| Build falha em `uv sync --frozen` | `uv.lock` desatualizado | `cd engine && uv lock` local, commit, push |
| Container reinicia em loop | `alembic upgrade` falhou | Logs do deploy → erro de migration ou DATABASE_URL mal-formada |
| `/healthz` retorna 502 | Postgres ainda não disponível | Railway leva ~30s para Postgres + nexus subirem juntos |
| `/auth/login` retorna 500 | `JWT_SECRET` ausente ou < 32 chars | Conferir variável |
| `/draft/llm` retorna 503 | `ANTHROPIC_API_KEY` ausente | Conferir variável |
| Stripe webhook retorna 400 | `STRIPE_WEBHOOK_SECRET` desalinhado | Recopiar do Stripe dashboard |
| Upload retorna 503 | Volume `CASO_DATA_DIR` não montado | Criar volume no Railway |

## Custos esperados (MVP, primeiros meses)

- **Railway compute:** US$ 5–15/mês (varia com tráfego)
- **Railway Postgres:** US$ 5/mês (1 GB; sobe quando passar)
- **Railway volume:** US$ 0,25/GB/mês
- **Anthropic Opus 4.8:** US$ 0,10–0,30 por peça gerada (com prompt caching)
- **Stripe:** 3,99% + R$ 0,39 por transação BR

**Cenário com 50 peças/mês:**
- Infra: ~US$ 12/mês
- LLM: ~US$ 7,50–15/mês
- Total fixo: ~US$ 20–30/mês

Para Sonnet 4.6 em vez de Opus, custo LLM cai ~60%.

## O que este doc não cobre (decisões futuras)

- **CDN / cache de static** (Railway não tem CDN nativo; CloudFront/Cloudflare em
  iteração futura quando o frontend existir)
- **Backups além do automático do Railway Postgres** (recomendado dump diário
  externo para S3/R2 antes de ter 10+ clientes pagantes)
- **Multi-region** (over-spec para o estágio atual)
- **Observabilidade externa** (Sentry/Logflare se a complexidade aumentar)
- **Frontend deploy** (Fase F do escopo — Vercel/Cloudflare Pages quando vier)
