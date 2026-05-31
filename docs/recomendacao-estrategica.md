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

**Nexus é infraestrutura interna do escritório Ribeiro & Tigre. Inova by Tigre é o produto
público.** Não invente uma terceira marca SaaS.

Por que essa estrutura é a certa para você agora:

1. **Inova by Tigre já tem chancela ConJur e está publicado.** É o produto que o mercado já
   reconhece. Nexus é o "como" por trás do "quê" (Inova).
2. **Monetização que sobrevive à OAB:** Inova é metodologia/treinamento/licença de método para
   outros advogados — **dentro** do que a OAB tolera (já está no ar). Marketplace SaaS de
   análise jurídica por crédito está **fora** sem parecer formal. Os dois modelos não são
   comparáveis em risco.
3. **Engine fica defensável:** Nexus como infra privada protege seu *know-how* (HALT, Dado
   Líquido, doutrina embutida) em vez de expô-lo num SaaS comoditizado. Capital intelectual
   composta — fica seu.
4. **HITL real:** advogado-operador segue responsável, que é a única forma de a OAB e o cliente
   final confiarem.

## As 4 ações das próximas 4-8 semanas (em ordem)

1. **Destravar push** — liberar o app GitHub OU aplicar o bundle que mandei. **Hoje.**
   Os 11 commits estão num container efêmero; perda real possível.
2. **Validar com Feito-HBM real** — rodar o engine localmente (Railway depois), pegar o caso já
   catalogado anonimizado, gerar peça em `/draft/llm` com fontes primárias do PJe, **você revisa,
   ajusta, assina, protocola**. Esse ciclo prova o produto antes de qualquer venda.
3. **Provisionar Railway com `NEXUS_TOKEN` + `CASO_DATA_DIR`** — infra privada do escritório,
   não exposta ao público. Ver `deploy.md`.
4. **Reposicionar a landing como porta da Inova by Tigre** — Nexus vira o motor mencionado no
   rodapé, não o protagonista. JSON-LD já está pronto para isso (commit `867cc42`).

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
