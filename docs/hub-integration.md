# HUB de Agentes × Cérebro Claude — Arquitetura de Integração

> Como o HUB de automação (Make, conta martbarreto@gmail.com) alavanca o engine Nexus
> (Claude) como cérebro de redação. Honesto sobre o que está construído e o que é roadmap.

## Visão geral

```
[Gatilho no HUB/Make]                        [Cérebro Claude]              [Saída no HUB]
Novo doc no Drive  ─┐                      ┌─ POST /draft/llm ─┐         ┌─ Gmail: rascunho
Email no Gmail     ─┼─▶ Make scenario ────▶│  engine Nexus     │────────▶┼─ Drive: salva minuta
Mensagem Slack     ─┘   (módulo HTTP)      │  HALT + quality   │         ├─ Slack: notifica
                                           └───────────────────┘         └─ Lumin: e-sign
```

## Divisão de trabalho

| Camada | Ferramenta | Papel | Estado |
|---|---|---|---|
| Orquestração / gatilhos | **Make (HUB)** | Dispara, roteia, conecta Gmail/Drive/Slack/Lumin | ✅ Conta conectada (OAuth) |
| Cérebro de redação | **Claude (engine Nexus)** | HALT, Dado Líquido, geração, quality_score | ✅ Construído; ⚠️ a hospedar |
| Conhecimento | **Drive** | Dossiês / fontes primárias (fora do repo) | ⚠️ Integração a desenhar |
| Entrega | Gmail / Lumin / Drive | Rascunho, assinatura, arquivo | ✅ Conexões disponíveis |

## Fluxo concreto

1. **Gatilho** — um cenário no Make observa um evento (novo doc no Drive, e-mail, msg Slack).
2. **Preparo do dossiê** — o cenário monta o payload com `feito_id` + `fatos[]`, cada fato
   com sua `fonte` primária (`certidao://`, `peticao://`, ...). **As fontes vêm de dados
   reais sob controle do operador — nunca de texto colado em chat.**
3. **Chamada ao cérebro** — módulo HTTP do Make → `POST https://<engine>/draft/llm`.
4. **Resposta do engine:**
   - `200` → `{ texto, quality: {score, gates}, ... }` → roteia para rascunho (Gmail/Lumin)
     para **revisão e assinatura do advogado-operador**.
   - `422` (HALT) → faltou Dado Líquido → notifica no Slack para purgação, não emite peça.
5. **Saída** — Make grava a minuta no Drive, cria rascunho no Gmail, ou inicia e-sign no Lumin.

## Regras inegociáveis nesta integração

1. **O Claude redige; você assina.** Nenhum cenário deve protocolar peça automaticamente.
   A saída do engine é sempre rascunho para revisão humana (responsabilidade técnica do
   advogado-operador).
2. **HALT é terminal.** Se o engine retorna 422, o cenário **não** contorna — encaminha
   para purgação. O valor do produto é justamente recusar gerar de fato não-líquido.
3. **PII fora do chat e com auth.** O `/draft/llm` processa dados sob segredo de justiça.
   Quando exposto à internet (Railway), exige autenticação e CORS restrito ao domínio do
   HUB — nunca aberto. Ver `deploy.md §"Onde discordo do relatório" ponto 3`.
4. **Drive como fonte, não como cérebro.** Drive guarda dossiês; a orquestração é do Make,
   a inteligência é do Claude. Drive não "orquestra agentes".

## Onde o Gemini caberia (opcional)

Como **segundo leitor** num módulo paralelo do Make — Gemini critica a minuta, Claude
redige — não como substituto do engine. É um padrão de verificação cruzada, opcional, e
fora do que esta sessão consegue construir (sem integração Gemini disponível aqui).

## Pré-requisitos para ligar (ordem)

1. Hospedar o engine (Railway) com `ANTHROPIC_API_KEY` em secret — `deploy.md`.
2. Adicionar auth + CORS ao `/draft/llm`.
3. No Make: criar cenário com módulo HTTP apontando para o engine; mapear gatilho e saída.
4. Catalogar o feito real em `$CASO_DATA_DIR` (fora do repo), com fontes primárias.
5. Testar com `quality_score` e HALT antes de plugar qualquer saída de entrega.

## Pendência para inventariar os "gens" reais

Listar os cenários (agentes) existentes no HUB exige o `teamId` do Make
(`app.make.com/team/{teamId}/...`). Com ele, mapeio cada cenário a este fluxo.
