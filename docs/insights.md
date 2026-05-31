# Nexus by Tigre — Depuração e Insights Evolutivos

> Documento vivo. Consolida o que aprendemos construindo o engine e a direção de
> evolução. Honesto sobre o que está pronto, o que é hipótese, e o que depende de você.

## 1. Onde estamos (estado real, não aspiracional)

| Camada | Estado | Evidência |
|---|---|---|
| Landing | ✅ Pronta | `index.html` — branding, lema, CTAs, rodapé OAB |
| Doutrina/protocolo | ✅ Documentado | `docs/` — protocolo, doutrina, tabela, casos, teses Feito-FB |
| Engine determinístico | ✅ Funcional | FastAPI + Jinja2 + HALT + Dado Líquido, 28 testes verdes |
| Engine LLM | ✅ Funcional* | Claude Opus 4.8 + adaptive thinking + prompt caching (*requer API key) |
| Quality gates | ✅ Funcional | 5 gates + quality_score, verificável |
| Catálogo de feitos | ✅ Anonimizado | RC / HBM / FB, vulnerabilidades como PENDENTE |
| CI / deploy | ⚠️ Parcial | Workflow Pages restaurado; CI (lint+test) ainda não |
| Push para remoto | ❌ Bloqueado | 403 da integração GitHub — ação sua |
| Google Workspace / Drive | ❌ Não construído | Fora do repo; exige OAuth e decisão de arquitetura |
| Feedback loop de outcomes | ❌ Não construído | Exige dados reais de êxito = LGPD + segredo de justiça |
| Pagamentos / marketplace | ❌ Não construído | Stripe/comissão — ver §4 e riscos OAB |

## 2. O insight central: HALT é o ativo, não o gargalo

Toda análise externa que recebemos trata "quantidade vs qualidade" como tensão a
resolver com mais infra (dashboards, scores, feedback loops). O insight que emerge de
construir o engine é mais simples e mais defensável:

> **O HALT já resolve a base da tensão. Ele não escala quantidade às custas da
> qualidade — ele se recusa a gerar quando o fato não é líquido.**

Isso inverte a lógica de mercado: em vez de "IA jurídica que produz mais rápido", o
produto é "IA jurídica que **se recusa a produzir lixo**". A garantia anti-alucinação é
o diferencial — e o `quality_score` é o complemento mensurável dela, não o contrário.

## 3. Depuração — pontos de fragilidade identificados

1. **"Temperatura Zero" é metáfora, não parâmetro.** Opus 4.8/4.7 removeram
   `temperature`. O determinismo vem de prompt rígido + estrutura. O nome do protocolo
   permanece; a implementação não usa `temperature=0`. Documentado, mas vale reforçar
   no material de marketing para não prometer o que a API não entrega.
2. **Catálogo em memória não escala.** `casos/data.py` é didático. Em produção, feitos
   vivem em `$CASO_DATA_DIR` (volume controlado), nunca no repo. Migração para storage
   real é pré-requisito de qualquer uso com dados reais.
3. **Quality gates são heurísticos.** Detectam presença de precedente, fonte, auditoria —
   não julgam mérito jurídico. `quality_score` é sinal pré-revisão, **não** substitui o
   advogado-operador. Vender como "validação automática de qualidade jurídica" seria
   overpromise e risco ético.
4. **Sem feedback loop = sem aprendizado.** O engine não melhora com êxito/derrota. Isso
   é intencional por ora (LGPD), mas limita a alegação de "aprende com +900 casos".

## 4. Direção evolutiva (priorizada por alavanca / risco)

1. **CI verde** (ruff + pytest no GitHub Actions) — barato, destrava confiança. Bloqueado só pelo push.
2. **Storage real para feitos** (`$CASO_DATA_DIR` → SQLite/Postgres) — pré-requisito de uso real.
3. **Mais templates de peça** (RHC, agravo, memoriais) — amplia cobertura; baixo risco.
4. **Contrato de dados anonimizado** — desenho que viabilize o feedback loop **sem** PII,
   para destravar a alegação de aprendizado sem violar LGPD/segredo.
5. **Camada de monetização** (ver `produto.md` §11) — depende de decisão de modelo e de
   parecer OAB sobre marketplace de pareceres.

## 5. Pergunta aberta que só você responde

O NotebookLM atual (para onde a landing aponta) é **substituído** pelo engine, é
**complementado** por ele, ou o engine vira o backend e o NotebookLM a UI? A resposta
muda a arquitetura de deploy da Fase 5.
