# 🏛️ Ecossistema NEXUM — Arquitetura & Papéis

> **Fotografia técnica do ecossistema.** Ribeiro & Tigre Advocacia Criminal ·
> Recife · Brasília · São Paulo. Documento de **onboarding e referência** para o
> titular/admin e futuros operadores. Sem dados sigilosos — não publicar peças,
> NPUs, valores ou credenciais neste repositório (vitrine pública · sigilo
> profissional / LGPD).
>
> Para **operar** a plataforma no dia a dia, comece pelo
> [Manual da Plataforma NEXUM](MANUAL-NEXUM.md). Este documento descreve a
> **arquitetura e a governança** — o *porquê* por trás do *como*.

---

## 0. Visão em uma frase

**NEXUM by Tigre** é a plataforma de **inteligência jurídica soberana** da Ribeiro
& Tigre, construída sobre três princípios inegociáveis — **local-first**,
**soberania de dados** e **IA explicável (XAI)** — onde um time híbrido (humanos +
IA roteada por especialidade) produz o contencioso de alta complexidade sob a
regra **dual-check**: nenhuma decisão de alto impacto sem **dois olhares
(humano + auditoria TIER 0)**.

---

## 1. Taxonomia das três camadas

O ecossistema é dividido em três camadas com fronteiras estritas. A separação
entre a **vitrine pública** (`supreme-drafter`) e a **esteira analítica**
(`warroom-tigre`, privado) é a linha de defesa do sigilo profissional.

| Camada | Onde vive | Repositório | Função |
|---|---|---|---|
| **1. Vitrine pública** | `public/` | `supreme-drafter` (público) | Site institucional V18 — servido via GitHub Pages. **Somente dados fictícios.** |
| **2. Ferramentas** | `tools/` | `supreme-drafter` (público) | Utilitários versionados que rodam na máquina do operador. |
| **3. Esteira de qualidade** | `.github/` | `supreme-drafter` (público) | CI de validação do site + peer-review TIER 0 que audita peças. |

> 🔒 **Fronteira de sigilo.** O trabalho real (peças, NPUs, casos) vive em
> `warroom-tigre` — repositório **privado** em Python, o sistema operacional da
> banca. Este repositório é **apenas a vitrine**. O acervo de pesquisa fica no
> **NotebookLM** (conta Google).

### 1.1 Camada 1 — Vitrine pública (`public/`)

Site estático no padrão de design **V18** (60-30-10 · `#090A0F` / menta `#10B981`
/ âmbar `#F59E0B` / carmesim `#EF4444` · tipografia mono). Tudo é **demonstração**.

| Página | Rota | Conteúdo |
|---|---|---|
| Início | `/` | Hero da War Room |
| NEXUM | `/nexum.html` | Landing institucional (pilares, arquitetura, JSON-LD SEO) |
| War Room | `/war-room.html` | Painel operacional (demo) |
| Controladoria | `/controladoria.html` | Gens: Custódia · Reconhecimento · Chronos (demo) |
| Grafo | `/grafo.html` | Grafo de Evidência Lógica XAI interativo (demo) |
| API | `/api.html` | Viewer OpenAPI 3.1 — spec em `public/openapi.json` |
| Planos | `/planos.html` | Tiers Core / Enterprise / Sovereign |
| 404 | `/404.html` | Erro com identidade da marca |

**Publicação:** push em `master` → workflow `pages.yml` (validate → publish em
`gh-pages`). **Domínio canônico:** `war.ribeiroetigre.org` (servido pelo próprio
GitHub Pages após o cutover de DNS + `public/CNAME`).

### 1.2 Camada 2 — Ferramentas (`tools/`)

| Ferramenta | Caminho | Função |
|---|---|---|
| **Degravação de audiências** | `tools/degravacao` | Transcreve áudio/vídeo em PT-BR (Gemini), com timestamps e identificação de depoentes → `.txt` + `.docx` (layout da banca). |
| **PDFs do site** | `tools/pdf` | Renderiza as páginas em PDF via Chrome headless (Puppeteer + pdf-lib) → artefato `nexum-pdfs` (7 páginas + combinado), gerado por `pdf.yml`. |

> ⚠️ Transcrição automática **não** dispensa conferência humana para uso processual.

### 1.3 Camada 3 — Esteira de qualidade (`.github/`)

Dois pipelines de CI independentes:

- **`Validate HTML & CSS`** — `html5validator` (Nu/W3C) em todo o repositório.
- **Peer-Review TIER 0** — auditoria dual-provider de peças jurídicas (§3).

---

## 2. Matriz de roteamento de IA

Princípio-régua: **qualidade onde a decisão é tomada; velocidade/custo onde a
tarefa escala.** O fluxo de montagem é uma linha:

```
Perplexity  →  pesquisa COM fontes (jurisprudência, fatos, precedentes)
     ↓
Claude      →  raciocínio + redação da peça (núcleo decisivo)
     ↓
Gemini      →  mídia e anexos (degravar áudio, ler PDF/imagem, Google/NotebookLM)
```

### 2.1 Papéis por ferramenta

| Integrante IA | Papel | Brilha em | Acesso |
|---|---|---|---|
| **Perplexity** | Pesquisador | Busca ao vivo com **fontes citadas** | `perplexity.ai` · apps · API Sonar |
| **Claude** | Redator / cérebro decisivo | Raciocínio longo, redação jurídica, análise de autos, código | `claude` (CLI) · claude.ai · IDE · API |
| **Gemini** | Multimodal | Áudio/PDF/imagem, contexto gigante, ecossistema Google | `gemini` (CLI) · gemini.google.com · API |

### 2.2 Régua de modelos Claude

> Não gastar o modelo caro no que o barato resolve — nem economizar no que decide.

| Modelo | ID | Use para |
|---|---|---|
| **Opus 4.8** (topo) | `claude-opus-4-8` | Peças decisivas (apelação, HC, contrarrazões, sustentação); autos extensos; estratégia multinível; arquitetura/refactor. |
| **Sonnet 4.6** (diário) | `claude-sonnet-4-6` | Edições, rascunhos, código moderado. |
| **Haiku 4.5** (volume) | `claude-haiku-4-5` | Tarefas em massa, baratas (resumo, formatação, classificação). |
| **Fable 5** (recente) | `claude-fable-5` | Alternativa recente — alternar e comparar. |

Alternar no Claude Code: `/model opus` (ou `/model claude-opus-4-8`) · `/fast`
(qualidade Opus com saída mais veloz).

---

## 3. Especificação do Dual-Check TIER 0

O peer-review automatizado (`.github/workflows/peer-review.yml`) audita cada Pull
Request com **dois modelos independentes** e consolida um veredito. **O merge só
passa com score consolidado ≥ 97/100** (configurável via `TIER0_GATE_SCORE`).

### 3.1 Arquitetura e lógica de concorrência

| Job | Provedor | Modelo | Autenticação |
|---|---|---|---|
| `claude-opus-review` | Anthropic | `claude-opus-4-8` | Repository secret `ANTHROPIC_API_KEY` |
| `gemini-pro-review` | Google (Vertex AI) | `gemini-3-pro` | **Workload Identity Federation** (zero secret) |
| `consolidation` | — | — | `GITHUB_TOKEN` interno |

Os dois jobs de revisão rodam **em paralelo** com `continue-on-error: true`. A
consolidação usa `if: always()`: **mesmo se um provedor falhar**, o relatório é
gerado (registrando a ausência). O gate **nunca fica refém de um único provedor**.

**Por que WIF no Gemini e secret no Claude:** usa-se o mecanismo mais seguro
disponível em cada provedor. Google suporta OIDC nativo (o `id-token: write` do
GitHub gera um token que a service account assume via WIF — **sem secret de longa
duração**). Anthropic não publica provedor OIDC; a única via da Messages API é a
chave `x-api-key`, logo Repository secret é o caminho canônico.

### 3.2 Gatilhos e roteamento

- `pull_request` (`opened`/`synchronize`/`reopened`) **apenas** quando o PR toca
  `pecas/**`, `engine/**` ou `nexum_engine/**`. PRs de site/ferramenta/doc **não**
  acionam o gate (não há peça a auditar).
- `workflow_dispatch` com input `pr_number` (botão manual na aba Actions).
- `issue_comment` filtrado para **`@gemini-cli /review`** (delegação Google CLI).

Roteamento automático por tipo de mudança:

- `pecas/*.pdf` → **pipeline jurídico** (XML semântico in → JSON de auditoria recursal out).
- `engine/*.py` ou `nexum_engine/*.py` → **pipeline de security review técnico**.
- Ambos → roda os dois.

### 3.3 Estados do gate (calibração de honestidade)

"Sem peça" e "provedor ausente" **nunca** são tratados como peça reprovada:

| Situação | Veredito | Comportamento |
|---|---|---|
| PR sem peça jurídica | ⚪ **NÃO APLICÁVEL** | passa (exit 0) |
| Peça presente, provedor(es) não configurado(s) | ⚪ **INCONCLUSIVO** | bloqueia (exit 1) |
| Peça presente e auditada | 🟢 ≥97 / 🔴 <97 | passa / bloqueia |

### 3.4 Pré-filtro LGPD determinístico

Todo PDF passa por um **pré-filtro determinístico ANTES de qualquer envio à API**:
mascara CPF, CNPJ, RG, telefone, e-mail e endereço; **preserva as OABs dos sócios
R&T (27.543 e 27.482)** por whitelist. É a materialização do princípio
**local-first**: dado sensível nunca sai em claro.

---

## 4. Integrantes da equipe — papéis

### 4.1 Humanos

| Integrante | Papel |
|---|---|
| **Marcelo Tigre** | Criador da plataforma · Engenheiro de Software Jurídico · sócio. Titular/**admin** (`nexum@ribeiroetigre.org`): executa o runbook de configuração (chaves, WIF, branch protection, domínio) pelos consoles GitHub/Google/Cloudflare — passos que o agente não faz. |
| **Ribeiro** (sócio) | Sócio da banca. OABs dos dois sócios (PE 27.543 e 27.482) preservadas por whitelist no pré-filtro LGPD. |
| **Operadores** (advogados/equipe) | Uso diário: War Room, degravação, redação e **revisão humana** das saídas de IA. |

### 4.2 IA (roteada por especialidade)

- **Perplexity** — pesquisador (fontes citadas).
- **Claude** — redator/cérebro decisivo (régua Opus/Sonnet/Haiku/Fable).
- **Gemini** — multimodal (mídia, anexos, Google/NotebookLM).
- **Dupla auditora TIER 0** — `claude-opus-4-8` + `gemini-3-pro` em concorrência,
  gate ≥ 97.

---

## 5. Princípios inegociáveis

- **Sigilo / LGPD:** peças, NPUs, valores e credenciais **nunca** neste repositório público.
- **Local-first:** dado sensível processado no endpoint do operador; em IA, contas/API com retenção e treino desabilitados.
- **Dual-check:** decisões de alto impacto passam por dois olhares (humano + TIER 0).

---

## 6. Mapa de documentos

- [`MANUAL-NEXUM.md`](MANUAL-NEXUM.md) — ponto de entrada: guia do operador + runbook do admin.
- [`stack-ia.md`](stack-ia.md) — roteamento de IA (Perplexity/Claude/Gemini, modelos).
- [`peer-review-workflow.md`](peer-review-workflow.md) — peer-review TIER 0 (arquitetura, gatilhos, estados, setup).
- [`../README.md`](../README.md) — visão do repositório, publicação e domínio.

---
_Ribeiro & Tigre Advocacia Criminal · NEXUM · Ecossistema — Arquitetura & Papéis_
