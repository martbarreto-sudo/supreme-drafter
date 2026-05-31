# Feito-FB — Arquitetura de Teses (anonimizado)

> Documento de trabalho **anonimizado**. Nenhum nome de paciente, vítima ou número
> processual real consta aqui. Identificadores reais ficam fora do repositório, no
> `$CASO_DATA_DIR` controlado pelo operador. Esta é a estrutura argumentativa; os
> fatos líquidos que a sustentam são auditados localmente contra fonte primária.

## Quadrante

Medidas protetivas (Lei Maria da Penha) — ataque à **estrutura nula do ato**, sem
tangenciar a credibilidade da suposta vítima.

## Modo de atuação

`[PERTINAZ]` — nulidades de instrução e prova; mimetismo micro-analítico (Toron) +
isolamento de teses (Tofic).

## Tese 1 — Ausência material de justa causa (mismatch subjetivo)

**Hipótese a auditar:** o documento que serve de substrato (representação/FONAR) estaria
emitido em desfavor/benefício de **terceiro estranho à lide**, não do Paciente.

- **Auditoria obrigatória (HALT):** confrontar a titularidade nominal do documento contra
  o nome do Paciente, extraindo a divergência diretamente do PJe. Sem o dado líquido, a
  tese **não avança** à fase dispositiva.
- **Se confirmado:** violação do *standard of proof* mínimo; substrato probatório inapto;
  configuração de representação sem sujeito passivo correspondente.
- **Ancoragem (Geraldo Prado):** a utilização de documento alheio para constranger o
  Paciente gera **contaminação por derivação** de toda a cadeia cautelar subsequente — o
  ato não é apenas nulo, é inexistente por ausência de correspondência subjetiva.

## Tese 2 — Nulidade por fundamentação genérica

**Hipótese a auditar:** a decisão liminar silenciaria sobre a divergência nominal e seria
genérica quanto ao substrato concreto.

- **Auditoria obrigatória (HALT):** verificar se o decisum enfrenta a divergência e
  fundamenta concretamente o periculum/fumus. Citação literal do trecho genérico, extraída
  da fonte primária.
- **Fundamento:** Art. 93, IX, CRFB/88 c/c Art. 315, §2º, CPP — dever de fundamentação
  específica; decisão que não dialoga com as particularidades do caso é nula.

## Escudo defensivo (compulsório)

**Tema 1249/STJ** como barreira: o ataque cinge-se ao **vício estrutural do ato estatal**.
Não se discute, em nenhum momento, a credibilidade da palavra da suposta vítima — o que
neutraliza o filtro do Tema 1249 e mantém a impetração no quadrante da nulidade objetiva.

## Pipeline de execução (no ambiente do operador)

1. Extrair os fatos do `record_index.json` → preencher `Feito-FB.vulnerabilidades` com
   `verificado` + `fonte` (peticao://, decisao://, certidao://).
2. `POST /draft/llm` com `peca_tipo: "HC"`, `modo: "PERTINAZ"`.
3. HALT bloqueia (422) se qualquer fato dispositivo ficar sem fonte líquida.
4. Revisar `quality.score` e a minuta. **A assinatura e a protocolização são ato do
   advogado-operador**, não do engine.

## Auditoria de Silêncio para este feito

- [ ] Titularidade nominal do documento de origem (espelho do PJe)
- [ ] Inteiro teor da decisão liminar (para citação literal)
- [ ] Cadeia de medidas cautelares derivadas (mapear contaminação)
- [ ] Termo de desinteresse / manifestação de órgão auxiliar, se houver
