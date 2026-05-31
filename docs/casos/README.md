# Índice de Feitos (anonimizado)

Esta pasta cataloga os feitos vivos da operação Nexus by Tigre em **forma anonimizada**. Nenhum número de processo real, nome de parte ou dado sensível é versionado neste repositório — apenas identificadores curtos e o quadrante dogmático.

Dados sensíveis ficam fora do repositório, em volume controlado pelo operador (ver `engine/data/` na fase de implementação do engine).

## Feitos catalogados

### Feito-RC — "Rota Caipira"
- **Quadrante:** Telemática / interceptação; marco temporal contestado
- **Eixo dogmático:** Tema 977/STF — distinguishing
- **Estado da auditoria:** PENDENTE — aguardando certidão de logs do PJe (extração bit-a-bit) para fixação documental do marco
- **Risco principal:** Litigância de má-fé caso o marco fixado divirja do log auditado
- **Operação:** insurgência telemática contra *live analysis* e manipulação de ERBs

### Feito-HBM — Caso-piloto (Tema 1.258/STF)
- **Quadrante:** Reconhecimento fotográfico; vício de origem no sumário da culpa
- **Eixo dogmático:** Tema 1.258/STF + HC 598.887/SC (STJ)
- **Estado da auditoria:** Reenquadrado — saiu da esteira de Execução Penal e voltou para Revaloração Jurídica do Reconhecimento Fotográfico
- **Risco principal:** Inépcia absoluta caso a peça seja distribuída no quadrante errado
- **Operação:** *distinguishing* estrito contra Tema 1.258; ataque ao sumário da culpa
- **Status no Supreme Drafter:** **caso-piloto** para a Fase 4 do engine (integração LLM)

### Feito-FB — "Barbalho"
- **Quadrante:** Robotização penal punitiva; fenômeno dos 4 minutos
- **Eixo dogmático:** Tema 1249/STJ como barreira horizontal
- **Estado da auditoria:** Estrutura mantida — fundamentação sobre retenção de termo de desinteresse de órgão auxiliar (NUDEM/DPPE)
- **Risco principal:** Esvaziamento do ataque caso o tema horizontal seja relativizado pelo tribunal
- **Operação:** aplicação horizontal do Tema 1249/STJ contra robotização

## Convenções

- **ID do feito:** sigla curta começando com `Feito-`
- **Dados reais:** ficam fora do repo, em `$CASO_DATA_DIR/<feito-id>/`
- **Dossiê, Relatório Ouro e Modo:** anexados ao volume de dados, nunca commitados
- **Cada feito** terá seu próprio arquivo `docs/casos/<feito-id>.md` quando atingir maturidade de catalogação pública (fora deste README)
