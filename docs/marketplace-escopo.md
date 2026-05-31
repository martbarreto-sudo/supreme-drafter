# Marketplace NEXUM — Escopo e Arquitetura do MVP

> Documento de escopo para a camada SaaS sobre o engine Nexum existente. Você assumiu
> explicitamente o risco regulatório OAB ao escolher esta direção
> (`docs/recomendacao-estrategica.md`). Este documento registra **como** mitigamos esse
> risco no design, sem bloquear o desenvolvimento.

## 0. Resumo executivo

- **O que é:** camada SaaS B2B sobre o engine Python/FastAPI já construído.
- **Para quem:** advogados criminalistas (não público leigo).
- **Posicionamento:** ferramenta de produtividade para advogados, **não** consultoria
  jurídica para usuário final. Esta distinção é arquitetural — está no modelo de
  cadastro, no TOS, no disclaimer de cada peça gerada.
- **Operador responsável:** advogado OAB cadastrado, não a plataforma.
- **Preserva:** 12 commits + 37 testes verdes + engine determinístico (HALT, Dado
  Líquido, quality_score, /autos, /draft/llm).

## 1. Posicionamento — a fronteira que NÃO atravessamos

### 1.1. O que somos

- Software-as-a-Service B2B para advogados criminalistas.
- Ferramenta de produtividade (similar a Astreapp, Juridoc, LegalCloud).
- Receita: assinatura mensal com volume incluído.

### 1.2. O que NÃO somos (e por quê)

- **Não somos consultoria jurídica.** Cobrar análise jurídica de leigo por IA cai em
  zona vermelha OAB. Vender ferramenta para advogado é zona aceita.
- **Não exercemos advocacia.** A peça gerada é minuta de trabalho do advogado,
  não opinião jurídica da plataforma.
- **Não substituímos advogado.** HITL é obrigatório — toda peça passa por revisão
  humana antes do protocolo.
- **Não vendemos análise direta ao público.** Cadastro exige OAB ativa.

### 1.3. Comparáveis legítimos no mercado brasileiro

Astreapp, Juridoc, ContratoSeguro, JusBrasil Pro — todos vendem software para
advogados, **não pareceres ao público**. É o enquadramento que sobrevive à OAB.

## 2. Riscos registrados e mitigações no MVP

| Risco | Mitigação arquitetural no MVP | Mitigação adicional recomendada |
|---|---|---|
| OAB regulamenta como consultoria | Cadastro exige OAB; TOS explícito; disclaimer em cada peça; HITL obrigatório | Conversar com Comissão de Tecnologia OAB/PE em paralelo |
| Captação irregular (Cód. Ética art. 5º) | Plataforma **não** entra em contato comercial automatizado com usuários; sem dashboard que veja casos individuais | TOS proibindo uso para captação |
| Veracidade de claims (CDC + OAB) | Planos vendem **apenas** o que engine faz (minuta com fontes + HALT + quality_score) | Não vender features inexistentes (estilometria, etc.) |
| Sigilo profissional | Dados de feitos isolados por user_id; criptografia em repouso | Acordo de confidencialidade no TOS; LGPD |
| Vazamento de credenciais | JWT com expiração curta; rotação de secret; senhas com bcrypt | 2FA opcional na Fase G |
| Cobrança como honorário disfarçado | Modelo de **assinatura mensal**, não preço por peça avulsa | Estrutura: cliente paga pelo software, não pelo "parecer" |

**Nota sobre o ponto 6:** vender "1 análise por R$ 199" se aproxima de honorário; vender
"plano Solo R$ X/mês com 10 peças incluídas" é estrutura SaaS padrão e sai dessa zona.
Por isso o MVP **não tem compra avulsa**.

## 3. Modelo de cliente

### 3.1. Quem cadastra
- Apenas advogados com OAB ativa.
- Validação no signup: número OAB + UF + nome.
- MVP: auto-declaração com aceite digital + verificação por amostragem.
- Fase G: integração API CNA-OAB (se disponível) ou parceria com cartório digital.

### 3.2. Quem assina TOS
- Advogado-operador confirma na primeira tela:
  > "Sou advogado(a) inscrito(a) na OAB sob nº [...], em situação regular. Sou
  > responsável técnico por toda peça gerada por este sistema. A plataforma é
  > ferramenta de produtividade; não exerce advocacia."

### 3.3. Quem usa o resultado
- Advogado revisa, ajusta, assina, protocola — sob sua OAB.
- Plataforma nunca protocola, nunca contata cliente do advogado.

## 4. Modelo de negócio (proposta inicial — calibrar antes de lançar)

### 4.1. Estrutura

- **Trial:** 14 dias, 3 peças geradas, sem cartão de crédito.
- **Assinatura mensal** com volume embutido.
- **Sem compra avulsa por peça** (decisão regulatória, ver §2).
- **Excedente:** cobrado no fim do ciclo (proporcional ao plano).

### 4.2. Planos (preços a calibrar com 10 advogados-beta)

| Código | Público | Peças/mês | Faixa preço-alvo* | Notas |
|---|---|---|---|---|
| `SOLO` | Advogado autônomo | 10 | R$ 300–500 | Entry-level |
| `BANCA` | Escritório 2-5 advogados | 50 | R$ 1.500–2.500 | Mais econômico/peça |
| `CORPORATE` | Banca > 5 advogados | 200 | R$ 6.000–10.000 | Negociado |

\* Faixas iniciais. **A calibrar empiricamente** com base em (a) custo real LLM,
(b) disposição-a-pagar de 10 advogados-beta, (c) preços de comparáveis.

### 4.3. Critérios de precificação

- **Custo LLM real (Opus 4.8 com prompt caching):** ~US$ 0,10–0,30 por peça.
- **Margem-alvo:** 70–80% (padrão SaaS B2B).
- **Sanity check:** preço por peça (preço/peças) deve ser sensivelmente **menor** que
  o que o advogado pagaria a um estagiário/assistente para gerar uma minuta análoga.
  Caso contrário, sem produto-mercado.

## 5. Modelo de dados

### 5.1. Entidades novas (PostgreSQL via SQLAlchemy)

```python
# engine/src/nexum/db/models.py — esboço, não código final

class User(Base):
    id: UUID  # PK
    email: str  # unique, lowercased
    name: str
    oab_numero: str
    oab_uf: str  # CHAR(2)
    oab_status: enum  # PENDING_DECLARATION, DECLARED, VERIFIED, REVOKED
    password_hash: str  # bcrypt
    created_at: datetime
    tos_aceito_em: datetime  # timestamp do aceite

class Subscription(Base):
    id: UUID
    user_id: UUID  # FK
    plan_code: str  # SOLO | BANCA | CORPORATE
    status: enum  # TRIAL | ACTIVE | PAST_DUE | CANCELED
    stripe_subscription_id: str  # nullable em TRIAL
    current_period_start: datetime
    current_period_end: datetime
    pecas_incluidas: int
    pecas_consumidas_no_periodo: int

class StripeEvent(Base):  # idempotência de webhook
    event_id: str  # PK, da Stripe
    type: str
    processed_at: datetime
    payload: JSONB

class Payment(Base):
    id: UUID
    user_id: UUID  # FK
    stripe_invoice_id: str
    amount_cents: int
    currency: str  # 'brl'
    status: enum  # PAID | REFUNDED | FAILED
    created_at: datetime

class Audit(Base):  # cada peça gerada
    id: UUID
    user_id: UUID  # FK
    feito_id: str
    fonte_uri: str  # hash://...
    quality_score: int
    halt_violations: JSONB
    minuta_path: str  # caminho em CASO_DATA_DIR
    created_at: datetime
```

### 5.2. Migration strategy

- Alembic para todas as migrations.
- `alembic upgrade head` no boot do container.
- Backup antes de migration destrutiva.

## 6. Endpoints — novos

### Auth (`/auth`)
- `POST /auth/signup` — cria User + envia email de confirmação
- `POST /auth/login` — retorna JWT (15min) + refresh token (30 dias)
- `POST /auth/refresh` — troca refresh por novo JWT
- `POST /auth/forgot-password` — envia link por email
- `POST /auth/reset-password` — completa reset
- `GET /auth/me` — perfil do usuário autenticado

### Billing (`/billing`)
- `POST /billing/checkout` — cria Stripe checkout session
- `POST /billing/webhook` — recebe eventos Stripe (idempotente via StripeEvent.event_id)
- `GET /billing/subscription` — status da assinatura atual
- `POST /billing/cancel` — cancela ao fim do período corrente
- `POST /billing/portal` — link para Stripe Customer Portal (gerenciar cartão)

### User (`/user`)
- `GET /user/profile`
- `PATCH /user/profile` — atualiza nome, OAB
- `GET /user/audits` — paginated, do mais recente
- `GET /user/audits/{id}` — detalhe + link para minuta

## 7. Endpoints existentes — modificações

| Endpoint | Hoje | Marketplace |
|---|---|---|
| `GET /healthz` | aberto | aberto |
| `POST /autos` | Bearer `NEXUM_TOKEN` | JWT do usuário; salva em `CASO_DATA_DIR/{user_id}/{feito_id}/{sha}.pdf` |
| `POST /draft/llm` | Bearer `NEXUM_TOKEN` | JWT do usuário; verifica plano ativo + decrementa `pecas_consumidas_no_periodo`; 402 se sem peças |
| `POST /draft` (determinístico) | Bearer `NEXUM_TOKEN` | Manter como admin/interno (não exposto a usuário) |

**Nota:** `NEXUM_TOKEN` continua existindo para endpoints administrativos (debug,
operações internas), separados do JWT de usuário.

## 8. Fluxos principais

### 8.1. Signup → Trial → Primeira peça

```
[User] POST /auth/signup
  └─→ valida email único, OAB válida, senha forte
  └─→ cria User(oab_status=PENDING_DECLARATION)
  └─→ envia email confirmação
  └─→ cria Subscription(status=TRIAL, pecas_incluidas=3, period_end=now+14d)

[User] clica link → confirma email → POST /auth/confirm
  └─→ User.oab_status = DECLARED

[User] POST /auth/login → JWT

[User] POST /autos (multipart PDF) com JWT
  └─→ valida JWT, extrai user_id
  └─→ salva em CASO_DATA_DIR/{user_id}/{feito_id}/{sha}.pdf
  └─→ retorna { fonte_uri: "hash://{feito_id}/{sha}" }

[User] POST /draft/llm com JWT + fonte_uri + autores etc
  └─→ valida JWT, busca Subscription ativa do user
  └─→ se pecas_consumidas >= pecas_incluidas: 402
  └─→ chama engine (HALT + Dado Líquido + LLM)
  └─→ se sucesso: incrementa pecas_consumidas, cria Audit
  └─→ retorna minuta + quality_score + disclaimer
```

### 8.2. Trial → Assinatura paga

```
[User] POST /billing/checkout { plan_code: "SOLO" }
  └─→ cria Stripe Checkout Session com client_reference_id=user_id
  └─→ retorna { url: stripe.com/... }

[User] paga no Stripe

[Stripe] POST /billing/webhook { type: "checkout.session.completed", ... }
  └─→ valida assinatura (constructEvent com STRIPE_WEBHOOK_SECRET)
  └─→ verifica StripeEvent.event_id (idempotência)
  └─→ se já processado: 200 imediato (no-op)
  └─→ retrieve session com expand=['line_items','subscription']
  └─→ atualiza/cria Subscription(status=ACTIVE, plan_code, stripe_subscription_id, period)
  └─→ cria Payment(stripe_invoice_id, amount, status=PAID)
  └─→ grava StripeEvent
  └─→ 200
```

### 8.3. Renovação mensal

```
[Stripe] POST /billing/webhook { type: "invoice.payment_succeeded" }
  └─→ idempotência via event.id
  └─→ atualiza Subscription.current_period_*
  └─→ reset pecas_consumidas_no_periodo = 0
  └─→ cria novo Payment
```

### 8.4. Falha de pagamento

```
[Stripe] POST /billing/webhook { type: "invoice.payment_failed" }
  └─→ Subscription.status = PAST_DUE
  └─→ /draft/llm passa a retornar 402 até regularização
  └─→ email ao usuário
```

## 9. Stack & dependências

```toml
# engine/pyproject.toml — adições

dependencies = [
    # existentes
    "anthropic>=0.50",
    "fastapi>=0.115",
    "pydantic>=2.9",
    "jinja2>=3.1",
    "python-multipart>=0.0.12",
    "uvicorn>=0.32",

    # novas — persistência
    "sqlalchemy[asyncio]>=2.0",
    "alembic>=1.13",
    "asyncpg>=0.30",

    # novas — auth
    "passlib[bcrypt]>=1.7",
    "python-jose[cryptography]>=3.3",
    "pydantic[email]>=2.9",

    # nova — billing
    "stripe>=11.0",
]
```

## 10. Variáveis de ambiente

```bash
# Existentes
ANTHROPIC_API_KEY=sk-ant-...
NEXUM_MODEL=claude-opus-4-8
NEXUM_TOKEN=...                   # endpoints administrativos
CASO_DATA_DIR=/data/feitos

# Novas — persistência e auth
DATABASE_URL=postgresql+asyncpg://user:pw@host:5432/nexum
JWT_SECRET=<256-bit-random>        # rotacionar a cada deploy ideal
JWT_ALGORITHM=HS256

# Novas — Stripe
STRIPE_SECRET_KEY=sk_live_...      # ou sk_test_ em sandbox
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_SOLO=price_...
STRIPE_PRICE_BANCA=price_...
STRIPE_PRICE_CORPORATE=price_...
STRIPE_CUSTOMER_PORTAL_URL=https://billing.stripe.com/p/login/...

# Nova — frontend (para redirect Stripe)
FRONTEND_URL=https://app.nexum.tigre.com  # placeholder; ver §14
```

## 11. Deploy

- **Plataforma:** Railway (já documentado em `docs/deploy.md`).
- **Postgres:** add-on gerenciado do Railway (com backups diários automáticos).
- **Secrets:** Railway environment variables.
- **CI:** GitHub Actions (já existe `.github/workflows/ci.yml`) — adicionar job de
  `alembic upgrade head` em deploy preview.
- **Monitoramento:** logs estruturados (JSON); métricas via Railway dashboard no MVP.

## 12. Cronograma proposto (6 fases, ~6 sessões)

### Fase A — Persistência e Auth básica
- Setup SQLAlchemy + Alembic
- Modelo User + StripeEvent
- Endpoints `/auth/signup`, `/auth/login`, `/auth/me`
- JWT middleware
- Testes (mock DB com pytest-asyncio + httpx)
- **Saída:** signup + login funcionando

### Fase B — Trial e gating
- Modelo Subscription
- Lógica de trial automático no signup (14d, 3 peças)
- Middleware JWT em `/autos` e `/draft/llm`
- Verificação de plano + decremento
- 402 quando sem peças
- Testes
- **Saída:** usuário consegue gerar 3 peças no trial

### Fase C — Stripe billing
- Endpoint `/billing/checkout`
- Endpoint `/billing/webhook` com idempotência via StripeEvent
- `customer.subscription.created` → ativa assinatura
- `invoice.payment_succeeded` → renova período + reset contador
- `invoice.payment_failed` → PAST_DUE
- `customer.subscription.deleted` → CANCELED
- Testes com `stripe-mock` ou mocks manuais
- **Saída:** usuário consegue assinar SOLO de verdade (em sandbox)

### Fase D — Histórico e perfil
- Modelo Audit
- Endpoint `GET /user/audits`
- Endpoint `GET /user/audits/{id}` com link para minuta
- Endpoint `PATCH /user/profile`
- Testes
- **Saída:** usuário vê histórico de peças

### Fase E — TOS, disclaimer, hardening
- TOS redigido por advogado humano (não IA) — você escreve, eu insiro
- Disclaimer obrigatório em **toda** peça gerada (já existe? checar template)
- Rate limiting (slowapi)
- LGPD: política de privacidade + endpoint de exportação/deleção de dados
- Logs de auditoria de acessos
- Testes
- **Saída:** plataforma juridicamente defensável

### Fase F — Frontend mínimo
- Next.js + Tailwind
- Páginas: signup, login, dashboard (lista de audits), upload, billing
- Sem dashboard admin no MVP
- Sem componentes de "intervenção comercial" no MVP (decisão §2)
- **Saída:** usuário consegue usar a plataforma sem curl

## 13. Fora do MVP (Fase G+)

- Dashboard admin (com regras claras de privacidade — não ver conteúdo de casos)
- OCR de PDF (extrair texto dos autos para alimentar /draft/llm automaticamente)
- Integração PJe (Tribunal Regional federais e estaduais via APIs públicas)
- Multi-tenant (escritório com múltiplos advogados sob uma conta corporativa)
- Workflow de aprovação interna (junior gera → sênior assina)
- Métricas de produto (Mixpanel/PostHog)
- Suporte humano (Intercom/Crisp)
- NF eletrônica (Plugnotas/FocusNF) — só quando volume justificar
- Marketing digital (Google Ads, etc.) — só depois de product-market fit comprovado
- 2FA, single sign-on, audit logs avançados

## 14. Decisões pendentes (preciso de você)

| Decisão | Opções | Minha sugestão |
|---|---|---|
| Nome do produto | Nexum / Nexus / Inova by Tigre | **Nexum** (alinha com docs e código) |
| Domínio frontend | `app.nexum.com.br` / `nexum.ribeiroetigre.org` / `app.inovabytigre.com` | `app.nexum.com.br` (registrar) |
| Validação OAB no MVP | API CNA / declaração assinada / verificação manual amostral | **Declaração assinada + amostragem manual** |
| Trial sem cartão | Sim / não | **Sim** (reduz fricção, padrão SaaS B2B) |
| Plataforma de pagamento | Stripe / PagSeguro / Iugu | **Stripe** (Pix + cartão; melhor dev-ex; aceita BRL nativamente) |
| Plano único ou múltiplos no MVP | 1 plano / 3 planos | **3 planos** (Solo/Banca/Corporate); precificação calibrada com beta |
| Quantas peças no trial | 1 / 3 / 5 | **3** (suficiente para o advogado avaliar a qualidade) |

## 15. O que **não** vamos fazer (registro explícito)

Itens que apareceram em blueprints externos e que **não entram** no MVP por decisão
arquitetural:

- **"Intervir / Oferecer Co-patrocínio" por WhatsApp** com base em casos vistos no
  dashboard — captação irregular (Cód. Ética OAB art. 5º).
- **Compra avulsa por peça** ("1 análise por R$ 199") — risco de honorário disfarçado.
- **Marketing como "auditoria forense"** ou "engenharia reversa processual" — vender
  features inexistentes; também posiciona como consultoria, não ferramenta.
- **"Estilometria forense", "Constrangimento Epistemológico"** — features inexistentes
  no engine, não vamos vender o que não fazemos.
- **Dashboard mostrando teses de outros advogados** — quebra de sigilo profissional.

---

## Como ler este documento

Não é especificação final. É **proposta** para você aprovar/ajustar antes de codar.

Se você aprovar como está, próximo passo é **Fase A** (Persistência + Auth básica).
Se quiser ajustar, me diga **qual seção** e **o que muda** — eu reescrevo.

Decisões da §14 (Decisões pendentes) podem ficar abertas no início, mas pelo menos
**Nome do produto** e **Trial sem cartão** afetam código da Fase A. As outras podem
esperar até Fase C (Stripe).
