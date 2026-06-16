# Peer-Review Automatizado Dual-Provider — NEXUM TIER 0

> Workflow `.github/workflows/peer-review.yml` · Ribeiro & Tigre Advocacia Criminal
> Recife · Brasília · São Paulo · OAB/PE 27.543

Audita cada Pull Request com **dois modelos independentes** (Claude Opus 4.8 e
Gemini 3 Pro) e consolida o resultado em um veredito TIER 0. O merge só passa se o
**score consolidado for ≥ 97/100**.

---

## 1. Arquitetura

| Job | Provedor | Modelo | Autenticação |
|---|---|---|---|
| `claude-opus-review` | Anthropic | `claude-opus-4-8` | **Repository secret** `ANTHROPIC_API_KEY` |
| `gemini-pro-review` | Google (Vertex AI) | `gemini-3-pro` | **Workload Identity Federation** (zero secret) |
| `consolidation` | — | — | `GITHUB_TOKEN` interno |

Os dois jobs de revisão rodam em paralelo com `continue-on-error: true`. O job de
consolidação usa `if: always()`, de modo que **mesmo se um provedor falhar**, o
relatório consolidado é gerado (registrando a ausência) — o peer-review nunca
fica refém de um único provedor.

### Gatilhos
- `pull_request: [opened, synchronize, reopened]`
- `workflow_dispatch` com input `pr_number` (botão manual na aba Actions)
- `issue_comment` filtrado para o texto **`@gemini-cli /review`** (delegação Google CLI)

### Roteamento automático por tipo de mudança
- PR toca `pecas/*.pdf` → **pipeline jurídico** (XML semântico in + JSON de auditoria recursal out)
- PR toca `engine/*.py` ou `nexum_engine/*.py` → **pipeline de security review técnico**
- Ambos → roda os dois

Todo PDF passa pelo **pré-filtro LGPD determinístico** ANTES de qualquer envio à
API: mascara CPF, CNPJ, RG, telefone, e-mail e endereço; preserva as OABs dos
sócios R&T (27.543 e 27.482) por whitelist.

---

## 2. Setup necessário (uma vez, pelo Dr. Marcelo)

### 2.1 Job 1 — Claude (Repository secret)
Em **Settings → Secrets and variables → Actions → aba Secrets → Repository secrets**:

| Nome | Valor |
|---|---|
| `ANTHROPIC_API_KEY` | chave Anthropic `sk-ant-...` |

> ⚠️ **Cadastre como Repository secret, não como Variable nem Environment.** O
> anti-padrão `len=0` (documentado no PR #14 e na skill) ocorre quando o valor
> está no cofre errado: o job pula em verde sem nunca ter chamado a API. O passo
> "Executar auditoria Claude" falha explicitamente se o secret estiver ausente.

Comando equivalente via CLI:
```bash
gh secret set ANTHROPIC_API_KEY --repo martbarreto-sudo/supreme-drafter
```

### 2.2 Job 2 — Gemini (Workload Identity Federation, zero secret)

Rode **uma única vez, fora do agente**, no projeto GCP do escritório:

```bash
.github/scripts/setup_workload_identity.sh \
  --repo "martbarreto-sudo/supreme-drafter" \
  --project "[PROJECT_ID]"
```

O script cria a service account (`roles/aiplatform.user`), o Workload Identity
Pool, o provider OIDC restrito a este repositório, a permissão de impersonation,
e imprime os dois valores a cadastrar em **Repository Variables** (texto claro,
não sensível — não são secrets):

| Variable | Exemplo |
|---|---|
| `GCP_WIF_PROVIDER` | `projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider` |
| `GCP_SERVICE_ACCOUNT` | `gemini-peer-review@PROJECT_ID.iam.gserviceaccount.com` |

```bash
gh variable set GCP_WIF_PROVIDER --repo martbarreto-sudo/supreme-drafter --body "projects/.../providers/github-provider"
gh variable set GCP_SERVICE_ACCOUNT --repo martbarreto-sudo/supreme-drafter --body "gemini-peer-review@PROJECT_ID.iam.gserviceaccount.com"
```

### 2.3 Gate configurável (opcional)
| Variable | Default | Função |
|---|---|---|
| `TIER0_GATE_SCORE` | `97` | Score consolidado mínimo para aprovar o gate |

---

## 3. Por que WIF para Gemini e secret tradicional para Anthropic

- **Anthropic não publica provedor OIDC** para federação de identidade; a única
  via de autenticação da Messages API é a chave `x-api-key`. Logo, Repository
  secret é o caminho canônico (mascarado nos logs, escopo de menor privilégio).
- **Google Cloud suporta OIDC nativo**: o `id-token: write` do GitHub gera um
  token que a service account assume via WIF. Isso **elimina o secret de longa
  duração** — não há chave para vazar, rotacionar ou expirar manualmente. É a
  evolução do redesign já recomendado no peer-review do thread-pai (OIDC GitHub ↔
  provedor de nuvem, "sem secret manual nunca mais").

Resumo: usa-se o mecanismo **mais seguro disponível em cada provedor** — WIF onde
há OIDC (Google), secret onde não há (Anthropic).

---

## 4. Como testar localmente

```bash
cd .github/scripts
pip install -r requirements.txt
python -m pytest tests/ -v --cov=. --cov-report=term-missing
```

Gate TIER 0: **≥ 10 testes verdes** e **cobertura ≥ 90 %**. Nenhum teste depende
de rede — os clientes de API são injetados como dublês determinísticos.

Roteamento manual de um PR:
```bash
printf 'pecas/hc.pdf\nengine/x.py\n' | \
  python .github/scripts/peer_review_orchestrator.py rotear
```

Consolidação manual de dois JSONs:
```bash
python .github/scripts/peer_review_orchestrator.py consolidar \
  --claude review_claude.json --gemini review_gemini.json \
  --out relatorio.md --gate 97
```

---

## 5. Próximos passos pós-merge

1. Cadastrar `ANTHROPIC_API_KEY` (secret) e as duas variables GCP.
2. Rodar `setup_workload_identity.sh` no GCP do escritório.
3. Abrir um PR de teste tocando um `pecas/*.pdf` e conferir os três comentários
   (Claude, Gemini, consolidado) no PR.
4. Tornar o check `Consolidação TIER 0` um **required status check** na branch
   protection de `master` (hoje só `Validate HTML & CSS` é obrigatório).
5. Sprint V2.0: cache de auditorias por hash de PDF; rótulo automático de PR por
   veredito; webhook Slack `#war-room`.
