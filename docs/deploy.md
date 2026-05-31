# Deploy — Fase 5 (decisões e ressalvas)

Resposta ao relatório de arquitetura. Separa o que adotamos do que é over-spec
para o estado atual do engine.

## Arquitetura adotada

```
GitHub push/PR ──▶ GitHub Actions (ci.yml: ruff + pytest)
                        │
landing estática ──▶ GitHub Pages (index.html + docs/)   [já configurado: pages.yml]
                        │
engine (FastAPI) ──▶ host de container persistente        [a provisionar]
                        └─▶ Claude API (Opus 4.8 / Sonnet 4.6 via NEXUS_MODEL)
```

## Decisões

| Item | Decisão | Observação |
|---|---|---|
| CI | **GitHub Actions** (`ci.yml`) | ruff + pytest no `engine/`. ✅ Implementado. |
| Frontend estático | **GitHub Pages** (`pages.yml`) | ✅ Workflow já restaurado; dispara em push para `master`. |
| Host do engine | **Railway** (recomendado) | Concordo: Railpack sem Dockerfile, billing por uso, container persistente. Ainda **não provisionado** — exige sua conta + secrets. |
| LLM | **Claude Opus 4.8** default; **Sonnet 4.6** via `NEXUS_MODEL` | Já suportado. Sonnet para reduzir custo conforme volume. |
| Secret da API | `ANTHROPIC_API_KEY` em secrets do host / GitHub | Nunca no repo, nunca no chat. |

## Onde discordo do relatório (over-spec para agora)

1. **Pydantic AI — não adotado.** O engine usa **Pydantic puro + SDK `anthropic` direto**.
   Para o escopo atual (request → minuta validada → quality gate) isso é suficiente e mais
   simples. Migrar para Pydantic AI seria rework por ganho marginal. Reavaliar só se
   surgir orquestração multi-step/multi-agente real.
2. **WebSockets / streaming bidirecional — desnecessário hoje.** O fluxo é request/response
   (`POST /draft/llm`). Streaming SSE pode entrar quando houver UI que renderize a peça
   token a token — não é pré-requisito de deploy.
3. **Pages consumindo a API do Railway em tempo real — atenção a CORS.** A landing atual é
   estática e **não chama nenhuma API**. Se for chamar o engine no Railway, configurar CORS
   no FastAPI e expor só os endpoints necessários (o `/draft/llm` processa PII — não deve
   ficar aberto à internet sem auth).
4. **Banco de dados (PITR, réplicas) — prematuro.** Sem feedback loop e sem storage real de
   feitos ainda (ver `insights.md §3`), não há o que persistir além de logs. Decidir o
   banco quando migrarmos o catálogo de `data.py` para storage real.

## Passos para provisionar (quando você decidir)

1. Criar projeto no Railway, conectar o repo, apontar root para `engine/`.
2. `railway variables set ANTHROPIC_API_KEY=...` (e `NEXUS_MODEL` se Sonnet).
3. Start command: `uv run uvicorn nexus.api:app --host 0.0.0.0 --port $PORT`.
4. Configurar CORS no FastAPI para o domínio do Pages, com auth no `/draft/llm`.
5. **Decisão de arquitetura pendente** (`insights.md §5`): o NotebookLM atual é
   substituído, complementado, ou vira UI deste engine? Isso define se o Pages chama o
   Railway ou continua só como vitrine estática.
