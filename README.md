# Supreme Drafter — Site público · Ribeiro & Tigre / NEXUM

Vitrine pública da plataforma **NEXUM by Tigre**, no padrão de design **V18**
(60-30-10 · `#090A0F` / menta `#10B981` / âmbar `#F59E0B` / carmesim `#EF4444` ·
tipografia mono). **Sem dados reais**: todos os painéis usam dados fictícios
rotulados como demonstração.

> 📘 **Comece pelo [Manual da Plataforma NEXUM](docs/MANUAL-NEXUM.md)** — guia
> único para operadores (uso diário) e admin (runbook de configuração).

## 🗺️ Mapa do repositório (pós-unificação das árvores)

Até 10/2026 este repositório abrigava **dois troncos sem ancestral comum**, e cada
sessão ou agente que entrava descrevia uma realidade diferente conforme o tronco em
que caísse. A branch `feature/unificacao-arvores` reconciliou os dois preservando
ambos os históricos (`merge -s ours --allow-unrelated-histories` + `read-tree --prefix`).

| Diretório | O que é | Estado |
|---|---|---|
| `public/` | Vitrine estática V18 publicada no GitHub Pages | **no ar** |
| `nexum_engine/` | Biblioteca de auditoria (hexagonal: `ports`/`adapters`, `verdade/gate`, `verdade/auditor`) — o **gatekeeper de citações** | **em uso** |
| `services/runtime/` | Pipeline CloudEvents v1.0: Outbox Relay, consumidor idempotente, DLQ com replay, OpenTelemetry, Helm/K8s, `docker-compose` com pgvector | **executável, não publicado** |
| `minutas/` | 20 peças processuais (HTML + PDF) | entregáveis |
| `tools/` | Degravação e geração de PDF | utilitário |

**Suíte unificada:** `pytest` na raiz coleta as duas árvores (140 testes).
Dependências do runtime: `pip install -r services/runtime/nexum/requirements.txt`.

> ⚠️ **A API de `public/openapi.json` é ROADMAP, não runtime.** As rotas ali descritas
> (`/messages/stream`, `rt_nx_auth`, barramento assíncrono) não estão implementadas em
> `public/`; o que roda é `nexum_engine` (biblioteca) e `services/runtime` (pipeline).
> A spec tem **uma fonte canônica** — `public/openapi.json`. As outras duas cópias
> (`public/api.html` como fallback e `services/runtime/docs/api-spec.json`) são
> **geradas** por `tools/sync-spec.py`; o teste de paridade falha se divergirem.

## 🌐 No ar (GitHub Pages)

**https://martbarreto-sudo.github.io/supreme-drafter/**

| Página | Rota | Conteúdo |
|---|---|---|
| Início | `/` | Hero da War Room |
| NEXUM | `/nexum.html` | Landing institucional (pilares, arquitetura, JSON-LD SEO) |
| War Room | `/war-room.html` | Painel operacional (demo) |
| Controladoria | `/controladoria.html` | Gens: Custódia · Reconhecimento · Chronos (demo) |
| Grafo | `/grafo.html` | Grafo de Evidência Lógica XAI interativo (demo) |
| API | `/api.html` | Viewer OpenAPI 3.1 — spec em [`/openapi.json`](public/openapi.json) |
| Planos | `/planos.html` | Tiers Core / Enterprise / Sovereign |
| 404 | `/404.html` | Erro com identidade da marca |

## 🔁 Publicação (automática)

Push em `master` → workflow [`pages.yml`](.github/workflows/pages.yml):
1. **validate** — `html5validator` (Nu/W3C) em todo o repositório (erros de CSS filtrados)
2. **publish** — sincroniza `public/` → branch `gh-pages` via `peaceiris/actions-gh-pages`
   (somente o `GITHUB_TOKEN` interno, sem secrets); o GitHub Pages (modo branch) publica
   em `github.io` — espelho secundário do site.

### 📄 PDFs do site (artefato de build)

Push em `master` (ou disparo manual) → [`pdf.yml`](.github/workflows/pdf.yml) renderiza
as páginas em PDF com Chrome headless (gerador versionado em [`tools/pdf/`](tools/pdf/),
Puppeteer + pdf-lib) e publica o conjunto como artefato **`nexum-pdfs`** (7 páginas + o
combinado `00-NEXUM-completo.pdf`). Esteira independente — não interfere no deploy do site.

## 🌍 Domínio próprio — `war.ribeiroetigre.org` (GitHub Pages)

O **domínio canônico** do site é **`war.ribeiroetigre.org`** (canonical, og:url,
sitemap e robots apontam para ele). Por ser uma **vitrine 100% estática**, o
próprio **GitHub Pages** serve o domínio próprio — com HTTPS gratuito, sem
segundo pipeline e sem nenhum secret. Não há mais deploy via Cloudflare Workers
(o caminho `wrangler` foi aposentado por ser desnecessário a um site estático).

**Estado atual:** o site está no ar em `martbarreto-sudo.github.io/supreme-drafter`.
O DNS de `war.ribeiroetigre.org` ainda **não resolve** (NXDOMAIN); por isso o
`public/CNAME` está **ausente** de propósito, mantendo o `github.io` no ar
(o Pages redireciona para o domínio próprio assim que o CNAME existir).

**Virada (cutover), quando quiser ativar o domínio próprio:**
1. No DNS (gerenciado na Cloudflare — apex já está lá): criar registro
   **`CNAME war → martbarreto-sudo.github.io`**, em modo **DNS only** (nuvem
   cinza, sem proxy) para o GitHub emitir o certificado.
2. Adicionar `public/CNAME` com o conteúdo `war.ribeiroetigre.org` e dar push em
   `master` → o publish leva o CNAME à `gh-pages` e o Pages assume o domínio.

## 🗺️ Onde fica o trabalho real (fora deste repo)

- **`warroom-tigre`** (repo privado, Python) — sistema operacional da banca.
  Para trabalhar nele com o Claude Code, **abra uma sessão apontada para ele**.
- **NotebookLM** (conta Google) — acervo de pesquisa.
- Este repositório é **apenas a vitrine pública** — não publicar aqui dados de
  casos, NPUs, valores ou credenciais (sigilo profissional / LGPD).

## 🧱 Estrutura

```
public/            ← tudo que vai ao ar (e somente isso)
  assets/styles.css  ← design system V18 compartilhado
  assets/app.js      ← comportamentos compartilhados (relógio · ano), com guardas
  *.html · openapi.json · robots.txt · sitemap.xml
.github/workflows/ ← CI + publicação (pages.yml · pdf.yml)
tools/pdf/         ← gerador dos PDFs do site (Puppeteer + pdf-lib)
```
