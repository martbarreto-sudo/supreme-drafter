# Stack de IA da banca — guia de roteamento

> Ribeiro & Tigre · NEXUM. Referência interna de **qual ferramenta/modelo usar em
> cada etapa**. Princípio: **qualidade onde decide, velocidade/custo onde escala.**
> _Não contém dados de casos, NPUs, valores ou credenciais._

## 1. Roteamento entre ferramentas

```
Perplexity  →  pesquisa COM fontes (jurisprudência, fatos, precedentes)
     ↓
Claude      →  raciocínio + redação da peça (núcleo decisivo)
     ↓
Gemini      →  mídia e anexos (degravar áudio, ler PDF/imagem, Google/NotebookLM)
```

| Ferramenta | Brilha em | Acesso |
|---|---|---|
| **Perplexity** | Busca ao vivo com **fontes citadas** | `perplexity.ai` · apps · API Sonar (`api.perplexity.ai`) |
| **Claude** | Raciocínio longo, redação jurídica, análise de autos, código | `claude` (CLI) · claude.ai · IDE · API |
| **Gemini** | Multimodal, contexto gigante, ecossistema Google | `gemini` (CLI) · gemini.google.com · API |

## 2. Qual modelo do Claude usar

Régua de eficiência: **não gastar o modelo caro no que o barato resolve — nem
economizar no que decide.**

| Modelo | ID | Use para |
|---|---|---|
| **Opus 4.8** (mais avançado) | `claude-opus-4-8` | Onde o erro custa caro / raciocínio profundo |
| **Sonnet 4.6** (diário) | `claude-sonnet-4-6` | Edições, rascunhos, código moderado |
| **Haiku 4.5** (volume) | `claude-haiku-4-5` | Tarefas em massa, baratas |
| **Fable 5** (recente) | `claude-fable-5` | Alternativa recente — alternar e comparar |

**Use Opus 4.8 em:**
1. Peças decisivas — apelação, HC, contrarrazões, sustentação.
2. Análise de autos extensos e teses contraditórias.
3. Estratégia processual multinível.
4. Arquitetura/refactor de código.

**Use Sonnet/Haiku em:** rascunho inicial, formatação, resumo de andamento,
degravação bruta, classificação. Suba para Opus só na lapidação final.

**Alternar no Claude Code:**
- `/model claude-opus-4-8` (ou `/model opus`) — sobe ao topo.
- `/fast` — modo rápido do Opus (qualidade Opus, saída mais veloz; Opus 4.8/4.7/4.6).

## 3. CLIs (instalar na máquina — uso diário)

```bash
npm install -g @google/gemini-cli   # Gemini
gemini -p "resuma este caso"        # headless (1 resposta)
cat autos.txt | gemini -p "extraia datas e prazos"

claude                               # Claude Code interativo
```
Autenticação Gemini: login Google **ou** `export GEMINI_API_KEY="…"` (AI Studio).

## 4. Privacidade (sigilo profissional / LGPD)

Para dados sigilosos de processo: usar **contas/API com retenção e treino
desabilitados**; **nunca** colar PII em contas gratuitas. Alinhado ao princípio
**local-first** do NEXUM.
