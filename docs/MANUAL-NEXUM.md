# 📘 Manual da Plataforma NEXUM — Ribeiro & Tigre

> **Comece por aqui.** Este é o ponto único de entrada da plataforma **NEXUM by
> Tigre**. Ensina **todos** a operar a solução e reúne o **runbook de
> configuração** (admin). Sem dados sigilosos — não publicar peças, NPUs, valores
> ou credenciais neste repositório (vitrine pública · sigilo profissional / LGPD).

| Você é… | Vá para |
|---|---|
| Advogado(a) / equipe (uso diário) | [§2 Guia do Operador](#2-guia-do-operador) |
| Titular / admin (`nexum@ribeiroetigre.org`) | [§3 Runbook do Admin](#3-runbook-do-admin) |
| Quer o mapa de docs | [§4 Mapa de documentos](#4-mapa-de-documentos) |

---

## 1. Visão geral

A plataforma tem três camadas:

1. **Vitrine pública** (`public/`) — site institucional V18 (NEXUM, War Room,
   Controladoria, Grafo XAI, API, Planos). No ar via **GitHub Pages**.
2. **Ferramentas** (`tools/`) — utilitários versionados que rodam na sua máquina:
   geração de **PDFs do site** e **degravação de audiências** (Gemini).
3. **Esteira de qualidade** (`.github/`) — CI que valida o site e o **peer-review
   TIER 0** (Claude Opus 4.8 + Gemini 3 Pro) que audita peças jurídicas.

---

## 2. Guia do Operador

### 2.1 Site / War Room
- No ar: **https://martbarreto-sudo.github.io/supreme-drafter/**
  (domínio próprio `war.ribeiroetigre.org` após o cutover — ver §3.4).
- Navegação: Início · NEXUM · War Room · Controladoria · Grafo · API · Planos.
- Tudo é **demonstração** (dados fictícios). Nunca colar caso real aqui.

### 2.2 Degravação de audiência (`tools/degravacao`)
Transcreve áudio/vídeo em PT-BR, com timestamps e **identificação dos depoentes**.
```bash
pip install -r tools/degravacao/requirements.txt
export GEMINI_API_KEY="sua_chave"        # https://aistudio.google.com/apikey
python3 tools/degravacao/degravar.py audiencia.mp4 --docx \
  -d "Juiz: Dr. Fulano; MP: Dr. Bruno; Defesa: Dr. Ayron; Vítima: Luan; Testemunha: Renan"
```
Gera `.txt` e `.docx` (layout da banca). `-m gemini-2.5-flash` p/ rapidez/custo.
> ⚠️ Transcrição automática **não** dispensa conferência humana para uso processual.

### 2.3 PDFs do site
Gerados automaticamente a cada push em `master` pelo workflow **`pdf.yml`**
(artefato **`nexum-pdfs`**: 7 páginas + combinado). Para gerar localmente:
```bash
cd tools/pdf && npm install && node generate.js   # saída em tools/pdf/dist-pdf/
```

### 2.4 Stack de IA — qual usar quando
Resumo (detalhe em [`stack-ia.md`](stack-ia.md)):

| Etapa | Ferramenta |
|---|---|
| Pesquisa **com fontes** (jurisprudência, fatos) | **Perplexity** |
| Raciocínio + **redação da peça** (decisivo) | **Claude Opus 4.8** (`/model opus`, `/fast`) |
| Edições/código do dia a dia | **Claude Sonnet 4.6** |
| Volume barato (resumo, formatação) | **Claude Haiku 4.5** |
| Mídia/anexos (áudio, PDF, Google) | **Gemini** |

### 2.5 Fluxo de uma peça com auditoria TIER 0
1. Redige a peça (Claude Opus) → revisão humana.
2. Quando a peça entra no fluxo auditável (`pecas/**` no repo **privado** da banca,
   **não** neste público), o **peer-review TIER 0** roda automaticamente:
   Claude Opus 4.8 **+** Gemini 3 Pro, com gate de score **≥ 97**.
3. Estados do gate (sem falso-reprovado): **NÃO APLICÁVEL** (sem peça) ·
   **INCONCLUSIVO** (provedor não configurado) · **🟢/🔴** (peça auditada).
   Detalhe em [`peer-review-workflow.md`](peer-review-workflow.md).
- Revisão sob demanda: comentar **`@gemini-cli /review`** no PR, ou
  *Actions → Peer-Review TIER 0 → Run workflow*.

---

## 3. Runbook do Admin

> Estes passos exigem o **console** (GitHub/Google/Cloudflare) logado como titular
> — não podem ser feitos pelo agente. Checklist mestre:

| # | Item | Onde | Necessário para |
|---|---|---|---|
| 3.1 | `ANTHROPIC_API_KEY` | GitHub → Secrets | Revisor Claude TIER 0 |
| 3.2 | WIF (2 variables) | GCP + GitHub → Variables | Revisor Gemini TIER 0 |
| 3.3 | Branch protection | GitHub → Branches | Tornar os checks obrigatórios |
| 3.4 | Domínio próprio | Cloudflare DNS + `public/CNAME` | `war.ribeiroetigre.org` no ar |

### 3.1 Chave da Anthropic (revisor Claude)
1. Gere a chave em **console.anthropic.com → API Keys**.
2. GitHub → **Settings → Secrets and variables → Actions → aba _Secrets_ →
   _Repository secrets_ → New repository secret**:
   - Nome: `ANTHROPIC_API_KEY` · Valor: a chave.
   - **Não** use *Environment secrets* nem a aba *Variables* (senão `${{ secrets.* }}` vem vazio → `len=0`).

### 3.2 Workload Identity Federation (revisor Gemini, sem secret)
Pré-requisito: `gcloud` autenticado e APIs habilitadas (`iam`, `iamcredentials`,
`sts`, `aiplatform`). Rode **uma vez**:
```bash
.github/scripts/setup_workload_identity.sh \
  --repo "martbarreto-sudo/supreme-drafter" --project "SEU_PROJECT_ID"
```
O script imprime os dois valores. Cadastre em **Actions → aba _Variables_ →
_Repository variables_** (NÃO secrets):
```bash
gh variable set GCP_WIF_PROVIDER     --repo martbarreto-sudo/supreme-drafter --body "projects/.../providers/github-provider"
gh variable set GCP_SERVICE_ACCOUNT  --repo martbarreto-sudo/supreme-drafter --body "gemini-peer-review@SEU_PROJECT_ID.iam.gserviceaccount.com"
```
(Opcional) `TIER0_GATE_SCORE` (variable, default `97`).

### 3.3 Branch protection (gate obrigatório)
GitHub → **Settings → Branches → Add rule** para `master`:
- ✅ *Require a pull request before merging*.
- ✅ *Require status checks to pass* → selecione **`Validate HTML & CSS`**
  (sempre) e, **somente após** 3.1 e 3.2 configurados, **`Consolidação TIER 0`**.
  > Não marque o TIER 0 como obrigatório antes das credenciais — bloquearia merges
  > com "INCONCLUSIVO". O gate já é honesto, mas required + sem credencial = trava.

### 3.4 Cutover do domínio `war.ribeiroetigre.org`
1. Cloudflare → **DNS → Add record**: `CNAME` · Name `war` · Target
   `martbarreto-sudo.github.io` · **DNS only** (nuvem cinza, p/ o cert do Pages).
2. Avise o agente (ou crie você): adicionar `public/CNAME` com
   `war.ribeiroetigre.org` e dar push → o Pages assume o domínio com HTTPS.
   > Não adicione o `public/CNAME` antes do DNS resolver — quebraria o `github.io`.

### 3.5 Verificação pós-setup
- Abra um PR de teste tocando `pecas/teste.pdf` (no repo privado) → o TIER 0 deve
  rodar e **auditar** (não mais "INCONCLUSIVO").
- `https://war.ribeiroetigre.org` deve responder com HTTPS após 3.4.

---

## 4. Mapa de documentos
- [`stack-ia.md`](stack-ia.md) — roteamento de IA (Perplexity/Claude/Gemini, modelos).
- [`peer-review-workflow.md`](peer-review-workflow.md) — peer-review TIER 0 (arquitetura, gatilhos, estados, setup).
- [`../tools/degravacao/README.md`](../tools/degravacao/README.md) — degravação de audiência.
- [`../README.md`](../README.md) — visão do repositório, publicação e domínio.

## 5. Princípios inegociáveis
- **Sigilo / LGPD:** peças, NPUs, valores e credenciais **nunca** neste repositório público.
- **Local-first:** dados sensíveis processados no endpoint do operador; em IA, usar contas/API com retenção/treino desabilitados.
- **Dual-check:** decisões de alto impacto passam por dois olhares (humano + TIER 0).

---
_Ribeiro & Tigre Advocacia Criminal · NEXUM · Manual da Plataforma_
