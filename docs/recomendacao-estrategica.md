# Recomendação Estratégica — leitura honesta do estado atual

> Você me autorizou ("Pondere tudo e veja o melhor pra mim"). Este documento é meu
> julgamento direto, sem opções para escolher. Curto de propósito.

## O que você tem (inventário honesto)

| Ativo | Estado | Valor real |
|---|---|---|
| **OAB/PE 27.543 + 600 sustentações + 100 júris** | Consolidado | Capital reputacional alto |
| **Ribeiro & Tigre** (Recife/Brasília/SP) | Operante | Banca real |
| **Inova by Tigre** (método 10 etapas, cobertura ConJur 2025) | Publicado, com mídia | Marca-metodologia consolidada |
| **Engine Nexus** (este repo, 11 commits) | Construído, 37 testes verdes | Infraestrutura técnica funcional |
| **Caso-piloto Feito-HBM** (Tema 1.258/STF) | Anonimizado, eixo dogmático claro | Validação real possível em dias |

Você **não é** uma startup pré-produto. Você é um advogado consolidado com método publicado e
engine funcional. O ponto de alavancagem não está em construir mais — está em conectar o que existe.

## O risco que vejo no padrão dos últimos 5 turnos

Uma IA externa empurrou, sequencialmente: marketplace de pareceres → frontend Next.js → Prisma →
Stripe → bio de SEO. Cada turno usa termos novos (Ferrajoli, garantismo, estilometria,
"constrangimento epistemológico") mas a estrutura é **a mesma**: SaaS público com cobrança
transacional sobre IA jurídica.

Isso é uma armadilha conhecida para fundador-solo em LegalTech:
- Os blueprints **parecem** tração (código pronto, planos de preço, telas).
- Na prática, são passivo técnico (bugs reais no webhook Stripe, claims de feature inexistentes)
  e passivo regulatório (cobrar análise por crédito ≠ honorário e cai na zona OAB).
- Você gasta o capital de atenção construindo um produto que **não é o seu**, enquanto o produto
  que **é o seu** (Inova by Tigre + Nexus como infra) fica parado.

## Minha recomendação

**Nexus é infraestrutura técnica deste repo. Inova by Tigre é metodologia
embrionária autoral do Marcelo Tigre — independente, não fundida com o Nexus.**

Por que separar:

1. **Inova by Tigre já tem chancela ConJur e está publicado** como **método**
   autoral do Marcelo (não como software). É produto de mentoria/treinamento
   que vive por mérito próprio.
2. **Nexus é a infra técnica** (este repo) — protocolo TIER 0 em código,
   com HALT + Dado Líquido + audit trail. Não precisa se apresentar como
   "implementação do Inova" para ter valor.
3. **Não fundir os dois evita dois riscos:**
   - **Conflito de marca** — Inova tem narrativa própria ("teoria dos jogos
     no processo penal"); Nexus é infra. Misturar reduz clareza de ambos.
   - **Exposição de know-how** — se Nexus for vendido como "Inova-em-código",
     compromete o moat da mentoria Inova.
4. **Monetização independente:**
   - Inova: metodologia/treinamento/licença — modelo já consolidado, OAB
     tolera.
   - Nexus: ferramenta de produtividade B2B para advogados (escopo §1) com
     gate OAB explícito — caminho separado.
5. **HITL real em ambos:** advogado-operador responsável.

## As 4 ações das próximas 4-8 semanas (em ordem)

1. **Destravar push** — liberar o app GitHub OU aplicar o bundle que mandei. **Hoje.**
   Os 11 commits estão num container efêmero; perda real possível.
2. **Validar com Feito-HBM real** — rodar o engine localmente (Railway depois), pegar o caso já
   catalogado anonimizado, gerar peça em `/draft/llm` com fontes primárias do PJe, **você revisa,
   ajusta, assina, protocola**. Esse ciclo prova o produto antes de qualquer venda.
3. **Provisionar Railway com `NEXUS_TOKEN` + `CASO_DATA_DIR`** — infra privada do escritório,
   não exposta ao público. Ver `deploy.md`.
4. **Reposicionar a landing** — sem fundir Inova com Nexus. A landing
   é da banca (Ribeiro & Tigre) e/ou do Nexus como infra. Inova vive
   no domínio próprio `inovabytigre.com`. Não criar fusão visual entre
   marcas que devem permanecer independentes.

## O que **adiar** (não eliminar — adiar)

- **Stripe / marketplace / créditos** — só depois de parecer formal da OAB/PE.
- **Frontend React/Next.js** — sem decisão de UX e sem deploy do backend, é trabalho prematuro.
- **Google Workspace / Drive sync / multi-tenant** — só faz sentido com múltiplos
  advogados-operadores ativos, que não é o caso ainda.
- **Mais turnos com IAs externas pedindo blueprints** — são prolixos, contraditórios e te
  empurram para o produto errado. Filtra.

## Detalhe operacional pendente que te custa hoje

- **A senha que você colou no chat dois turnos atrás precisa ser trocada agora.** Está no
  histórico. Vá em `myaccount.google.com → Segurança → Senha`. Ative 2FA se ainda não tiver.

## O que isto não é

Isto é um **julgamento**, não uma certeza. Você é o operador e a decisão é sua. Se discordar de
qualquer parte, me diga **qual** parte e por quê — discutimos. Mas precisa ser sua decisão, não
o próximo blueprint copiado de IA externa.
