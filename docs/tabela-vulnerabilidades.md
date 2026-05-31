# Tabela de Desconstrução de Vulnerabilidades

Template padrão para auditoria pré-minuta. Toda peça gerada pelo Supreme Drafter deve trazer (em anexo de trabalho, não na peça final) uma tabela preenchida neste formato.

## Cabeçalho

- **Feito:** `<ID-anonimizado>` (ex.: Feito-RC, Feito-HBM, Feito-FB)
- **Modo:** `<tipo de peça>` (HC, RHC, Agravo, etc.)
- **Data da auditoria:** `<YYYY-MM-DD>`
- **Operador:** `<sigla>`

## Tabela

| # | Fato Proposto (Comando) | Realidade Fática Verificada | Fonte Primária | Status | Impacto Jurídico / Risco de Inadmissibilidade |
|---|---|---|---|---|---|
| 1 | _ex.: Fixação do marco telemático em 25/06/2025_ | _ex.: Log do PJe não auditado_ | `log_pje://...` | **PENDENTE** | Litigância de má-fé; fulmina o distinguishing contra Tema 977/STF |
| 2 | _ex.: Aplicação da Súmula 231/STJ ao Processo X_ | _ex.: Autos pertencem ao Tema 1.258/STF_ | `certidao://...` | **DESCARTADO** | Inépcia absoluta; rejeição liminar |
| 3 | ... | ... | ... | ... | ... |

## Legenda de status

- **LÍQUIDO** — fato confrontado contra fonte primária e confirmado
- **PENDENTE** — aguardando inserção/extração de fonte; HALT ativo
- **DESCARTADO** — fato diverge da fonte; não pode constar da minuta

## Regra de fechamento

A minuta **não é assinada** enquanto houver pelo menos um fato em PENDENTE ou DESCARTADO referenciado em trecho dispositivo. Fatos descartados podem permanecer apenas em seção argumentativa marcada como hipótese.

## Auditoria de Silêncio (apêndice obrigatório)

Listar abaixo o que o dossiê **não** entregou e que poderia ser determinante:

- [ ] Certidão de trânsito em julgado
- [ ] Hash/espelhamento forense da fonte primária
- [ ] Termo de desinteresse de órgão auxiliar (NUDEM, DPPE, etc.)
- [ ] Marco temporal documental (decadência, prescrição)
- [ ] Inteiro teor de jurisprudência citada
- [ ] Outros: `<descrever>`
