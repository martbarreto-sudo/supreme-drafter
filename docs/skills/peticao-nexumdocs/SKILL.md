---
name: peticao-nexumdocs
description: Produção de peças processuais criminais no padrão NexumDocs (Ribeiro & Tigre). Usar quando solicitado para produzir petições, HCs, memoriais, embargos, agravos ou qualquer peça processual criminal. Aplica formatação limpa para protocolo PJe, prosa artesanal (voz do Tigre), tabelas Visual Law e negritos estratégicos.
---

# Peticao NexumDocs — Padrão Definitivo de Peças Processuais

## Identidade da Marca = VOZ DO TIGRE

A excelência NÃO está em firulas gráficas. Está na PROSA ARTESANAL e na ESTRUTURA ARGUMENTATIVA. Formato limpo para PJe — sem cabeçalho gráfico, sem rodapé gráfico, sem numeração de páginas.

### Vocabulário Característico

Expressões recorrentes: "denodo e respeito de estilo", "sobremodo enviesada", "sofreguidão acusatória", "orfandade probatória", "esquizofrenia fática". Latim: ex vi, fumus boni iuris, periculum in mora, data venia. Ironia controlada devastadora. Perguntas retóricas que destroem a narrativa acusatória.

### Negritos Estratégicos

Usar negrito APENAS em palavras-chave que o magistrado absorve em scanning rápido. Nunca em frases inteiras. O negrito é bisturi, não marreta.

## Formatação PDF (Protocolo PJe)

| Elemento | Especificação |
|----------|---------------|
| Fonte | Times New Roman 12pt corpo |
| Títulos | Times New Roman 12pt negrito, caixa alta |
| Espaçamento | 1.5 entre linhas |
| Margens | 3cm superior/esquerda, 2cm direita/inferior |
| Tabelas | Bordas simples 0.5pt, sem fundo colorido, headers em negrito |
| Alinhamento | Justificado |
| Cabeçalho gráfico | NENHUM |
| Rodapé gráfico | NENHUM |
| Numeração de páginas | NENHUMA (PJe numera) |
| Extensão | 10-14 páginas |

## Estrutura Obrigatória

### 1. Endereçamento

Centralizado, caixa alta, negrito: `EXCELENTÍSSIMO SENHOR DOUTOR [CARGO] DA [VARA/CÂMARA/TURMA] — [TRIBUNAL]`

### 2. Dados do Processo

Centralizado: Processo nº, Partes conforme tipo de peça.

### 3. Preâmbulo

Sempre iniciar com qualificação + "comparece à presença de Vossa Excelência, com o denodo e o respeito de estilo, para apresentar..."

### 4. Corpo (seções numeradas em romano)

Cada seção com título descritivo em caixa alta que já antecipa a tese. Mínimo 3 seções substantivas.

### 5. Tabelas Visual Law

Inserir no mínimo 2 tabelas: (a) Tabela de Auditoria (Alegação vs Prova Técnica); (b) Matriz de Síntese Defensiva (eixos temáticos cruzados).

### 6. Requerimentos

Alíneas a, b, c com fundamentação legal inline e recuo.

### 7. Fechamento

```
Nestes Termos, Pede Deferimento.
[Cidade/UF], [data].

Marcelo Tigre — OAB/PE 27.543
Ydigoras Ribeiro Jr. — OAB/PE 27.482
Assina eletronicamente no PJe.
```

## Referências Cruzadas (MATRIX)

- Análise prévia do caso: skill `metodo-tigre` (Fases 1-4)
- Fluxo operacional: skill `nexum-operacional`
- Dossiês digitais: skill `dossie-criminal-rt`
- Pesquisa jurisprudencial: skill `engenharia-juridica`

## Geração do PDF

Usar `scripts/gerar_peticao.py` com reportlab. Ver `references/especificacoes_formatacao.md` para detalhes técnicos completos.
