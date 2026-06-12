# Supreme Drafter — Site público · Ribeiro & Tigre / NEXUM

Vitrine pública da plataforma **NEXUM by Tigre**, no padrão de design **V18**
(60-30-10 · `#090A0F` / menta `#10B981` / âmbar `#F59E0B` / carmesim `#EF4444` ·
tipografia mono). **Sem dados reais**: todos os painéis usam dados fictícios
rotulados como demonstração.

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

## ☁️ Deploy primário — Cloudflare (`war.ribeiroetigre.org`)

O **domínio canônico** do site é **`war.ribeiroetigre.org`** (canonical, og:url,
sitemap e robots apontam para ele), servido via **Cloudflare Workers (Static
Assets)** por [`deploy-cloudflare.yml`](.github/workflows/deploy-cloudflare.yml) +
[`wrangler.jsonc`](wrangler.jsonc) — subdomínio dedicado, sem tocar o apex. O
GitHub Pages (`github.io`) permanece como espelho secundário.

O deploy Cloudflare só executa quando existir o **Repository secret
`CLOUDFLARE_API_TOKEN`** (Settings → Secrets and variables → Actions →
*Repository secrets* — **não** *Environment*, **não** a aba *Variables*). Sem o
secret, o job **pula em verde** e o diagnóstico imprime `len=0`; o workflow lê o
token via `${{ secrets.CLOUDFLARE_API_TOKEN }}` no escopo do job, sem declarar
`environment:`, então um **Repository secret** é exatamente o que ele consome.
Após cadastrá-lo, dispare por **Actions → "Run workflow"** (ou um novo push) —
como o job pula (não falha) sem o secret, "Re-run failed jobs" não se aplica.

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
.github/workflows/ ← CI + publicação (pages.yml · pdf.yml · deploy-cloudflare.yml)
tools/pdf/         ← gerador dos PDFs do site (Puppeteer + pdf-lib)
wrangler.jsonc     ← config Cloudflare Workers (Static Assets · war.ribeiroetigre.org)
```
