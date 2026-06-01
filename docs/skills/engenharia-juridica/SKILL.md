---
name: engenharia-juridica
description: "Sistema de cruzamento temático-fatual para advocacia criminal. Usar para organização de arquivos jurídicos por tese, síntese de precedentes com dados concretos, redação de petições com fusão fato-norma, gestão de Drive com taxonomia temática."
---

# Engenharia Jurídica

Sistema de precisão para advocacia criminal que opera sob o paradigma de **cruzamento temático-fatual**.

## Princípios Fundamentais

### Imperativo da Concreção
Jamais cite tese abstrata sem o **Dado Líquido** do caso concreto. Toda argumentação exige:
- Input A: Fato bruto extraído dos autos
- Input B: Precedente vinculante (STJ/STF)
- Output: Parágrafo de subsunção aplicando B sobre A

### Estilo Tier 0
Adotar tom de Tribunais Superiores. Cortar advérbios desnecessários. Foco na subsunção do fato à norma.

## Taxonomia de Arquivos

### Nível 1: Macro-Teses (Pastas Raízes)
```
NULIDADES/
PRISAO_CAUTELAR/
PROVAS_DIGITAIS/
CRIMES_FINANCEIROS/
TRIBUNAL_JURI/
EXECUCAO_PENAL/
```

### Nível 2: Precedentes Vinculantes
Dentro de cada macro-tese, agrupar por precedente-chave:
```
NULIDADES/
├── HC_598051_BUSCA_SEM_MANDADO/
├── HC_612234_HASH_CADEIA_CUSTODIA/
└── HC_587456_INTERCEPTACAO_FUNDAMENTACAO/
```

### Nível 3: Dados Líquidos (Casos)
Subpastas com dados concretos que se encaixam na tese:
```
NULIDADES/HC_598051_BUSCA_SEM_MANDADO/
├── PRECEDENTE_STJ.pdf
├── CASO_PATRICK_XAVIER_LAUDO.pdf
└── CASO_ROMARIO_AUTO_BUSCA.pdf
```

### Convenção de Nomenclatura
`[TESE]_[PRECEDENTE_CHAVE]_[DADO_CONCRETO_REF]`

Exemplo: `NULIDADE_HC598051_PATRICK_LAUDO_PERICIAL.pdf`

## Protocolo de Fusão

Em toda resposta que envolva argumentação jurídica, executar automaticamente:

**Estrutura Obrigatória:**
```
FATO LÍQUIDO: [Descrição objetiva do fato extraído dos autos]
PRECEDENTE: [Número do HC/REsp + Ministro Relator + Tese fixada]
SUBSUNÇÃO: [Parágrafo aplicando o precedente ao fato concreto]
```

**Exemplo:**
```
FATO LÍQUIDO: O réu entregou passaporte em 15/03/2024 e permanece 
custodiado há 11 meses sem instrução concluída.

PRECEDENTE: HC 143.333/BA, Min. Sebastião Reis Júnior - "A prisão 
preventiva deve guardar contemporaneidade com os fatos que a 
fundamentaram, sob pena de se converter em antecipação de pena."

SUBSUNÇÃO: No caso vertente, a entrega espontânea do passaporte 
demonstra inexistência de risco de fuga, enquanto o decurso de 11 
meses sem conclusão da instrução revela ausência de contemporaneidade 
entre o decreto prisional e a situação fática atual, impondo-se a 
revogação da custódia cautelar nos termos do precedente citado.
```

## Workflow de Organização de Drive

1. **Identificar Macro-Tese:** Classificar arquivo na categoria temática principal
2. **Vincular Precedente:** Associar ao precedente STJ/STF mais relevante
3. **Indexar Dado Líquido:** Extrair o fato concreto que se amolda à tese
4. **Posicionar:** Mover para estrutura `MACRO-TESE/PRECEDENTE/CASO`

## Workflow de Redação

1. **Extrair Fatos Líquidos:** Listar todos os fatos objetivos dos autos
2. **Mapear Precedentes:** Para cada fato, identificar precedente aplicável
3. **Executar Fusão:** Gerar parágrafo de subsunção para cada par fato-precedente
4. **Estruturar Petição:** Organizar em seções com índice de incidências

## Estrutura de Petição Padrão

```markdown
# EMENTA DO PEDIDO
[Síntese em 3 linhas do pedido principal]

# ÍNDICE DE INCIDÊNCIAS FÁTICAS
| Fato Líquido | Precedente | Página dos Autos |
|--------------|------------|------------------|
| [Fato 1]     | [HC/REsp]  | [fl. XX]         |

# DESENVOLVIMENTO
## I - DOS FATOS
[Narrativa objetiva]

## II - DA SUBSUNÇÃO NORMATIVA
[Aplicação de cada precedente aos fatos]

## III - DO PEDIDO
[Pedido específico com fundamento]
```

## Mapa de Precedentes por Tema

### Prisão Cautelar
- **Contemporaneidade:** HC 143.333/BA (Min. Sebastião Reis)
- **Fundamentação Genérica:** HC 152.752/PR (Min. Gilmar Mendes)
- **Excesso de Prazo:** HC 137.728/PE (Min. Rogerio Schietti)

### Nulidades
- **Busca sem Mandado:** HC 598.051/SP (Min. Sebastião Reis)
- **Hash/Cadeia Custódia:** HC 612.234/RJ (Min. Rogerio Schietti)
- **Interceptação:** HC 587.456/MG (Min. Joel Paciornik)

### Provas Digitais
- **Algoritmo/IPED:** RHC 143.169/RJ (Min. Nefi Cordeiro)
- **WhatsApp sem Autorização:** RHC 51.531/RO (Min. Nefi Cordeiro)
- **Espelhamento Indevido:** HC 652.284/SC (Min. Rogerio Schietti)

## Scripts Disponíveis

### organizar_drive.py
Reorganiza arquivos do Google Drive seguindo taxonomia temática.
```bash
python scripts/organizar_drive.py --pasta "PREVENTIVA" --destino "PRISAO_CAUTELAR"
```

### gerar_indice.py
Gera índice de incidências fáticas a partir de PDF dos autos.
```bash
python scripts/gerar_indice.py --autos "processo.pdf" --output "indice.md"
```

### fusao_tese.py
Executa protocolo de fusão fato-precedente.
```bash
python scripts/fusao_tese.py --fato "texto do fato" --tema "prisao_cautelar"
```
