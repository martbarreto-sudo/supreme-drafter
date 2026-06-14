# Changelog — Workflow Peer-Review TIER 0

Todas as mudanças relevantes do workflow `.github/workflows/peer-review.yml` e do
orquestrador `.github/scripts/peer_review_orchestrator.py`.

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) ·
versionamento [SemVer](https://semver.org/lang/pt-BR/).

## [1.0.0] — 2026-06-14

### Adicionado
- Workflow `.github/workflows/peer-review.yml` com 3 jobs paralelos:
  - **Job 1 `claude-opus-review`** — Claude Opus 4.8 (`claude-opus-4-8`) via
    Anthropic Messages API, autenticado por Repository secret `ANTHROPIC_API_KEY`.
  - **Job 2 `gemini-pro-review`** — Gemini 3 Pro (`gemini-3-pro`) via
    `google-github-actions/run-gemini-cli@v0`, autenticado por **Workload
    Identity Federation** (`google-github-actions/auth@v2`), **zero secret**.
  - **Job 3 `consolidation`** — consolidador TIER 0 (`needs` + `if: always()`),
    gera relatório markdown com convergências/divergências e aplica o gate ≥ 97.
- Gatilhos: `pull_request [opened, synchronize, reopened]`, `workflow_dispatch`
  (input `pr_number`) e `issue_comment` filtrado para `@gemini-cli /review`.
- Roteamento automático: `pecas/*.pdf` → pipeline jurídico; `engine|nexum_engine/*.py`
  → security review; ambos → os dois.
- Orquestrador Python com 5 classes: `LGPDAnonimizer`, `PecaExtractor`,
  `ClaudeReviewer` (XML in / JSON out, pré-fill `{`), `GeminiReviewer`
  (gemini-cli headless), `TIER0Consolidator` (merge + tabela markdown).
- Pré-filtro LGPD determinístico com whitelist das OABs dos sócios R&T
  (27.543 e 27.482).
- System prompt canônico versionado em `system_prompts/auditor_juridico_rt.md`.
- Script `setup_workload_identity.sh` para configuração WIF (uma vez, no GCP).
- Suíte de 25 testes pytest (cobertura 94 % no orquestrador, gate TIER 0 ≥ 90 %).
- Documentação de setup em `docs/peer-review-workflow.md`.

### Decisões técnicas
- **WIF para Gemini, secret para Anthropic**: usa-se o mecanismo mais seguro
  disponível em cada provedor — OIDC/WIF onde há (Google), secret onde não há
  provedor OIDC público (Anthropic). Evolução do redesign OIDC do thread-pai.
- **`continue-on-error: true`** nos jobs de revisão + **`if: always()`** na
  consolidação: peer-review dual nunca fica refém de um único provedor.
- **Jurisprudência canônica preservada**: HC 598.051/SP (6ª Turma, j. 02/03/2021,
  DJe 15/03/2021), SV 14/STF, Tema 990 = RE 1.055.941/STF.

[1.0.0]: https://github.com/martbarreto-sudo/supreme-drafter
