# Auditoria — Gems e Skills do Drive vs. Protocolo TIER 0

> Auditoria de conformidade dos 8 Gems Gemini + 3 Skills `.skill` que vivem no
> Drive de `martbarreto@gmail.com`, contra o protocolo doutrinário
> `docs/tier-0-protocolo.md`. Objetivo: identificar o que **manter como está**,
> o que **refinar** e o que **portar para o engine** Nexus.

Critério de conformidade: as 7 camadas do TIER 0 (identidade + princípio raiz,
estilo, formato, verificação, auditor adversarial, papéis, segurança).

---

## Mapa rápido — papel de cada Gem no ciclo TIER 0

| Camada/Papel TIER 0 | Gem que cumpre | Status |
|---|---|---|
| 5 / ESTRATEGISTA | `M Advogado Criminalista amplificado` | parcial |
| 5 / REDATOR | `⚖️ Redator de Elite` | parcial (alinha mas com ressalvas) |
| 5 / AUDITOR | `⇍AUDITOR FORENSE⇍` | bom alinhamento |
| 5 / VERIFICADOR | `🕵️ DEEP HUNTER` + `Analista Primário` | combinados, cumprem |
| Suporte técnico | `PERÍCIAS DIGITAIS` + `Engenharia Reversa` (Python) | utilidades |
| Fora do escopo Nexus | `🕵️ PROJETO BEATRIZ TIGRE` (PAS/UnB) | manter isolado |

---

## 1. `⚖️ Redator de Elite` — REDATOR (Camada 5)

**Função declarada:** Gêmeo Digital, materializa defesa a partir do Dossiê do
DEEP HUNTER. Mimetiza técnica Toron + combatividade Kakay + precisão Tofic.

**Modos operacionais:**
- `MODO PERTINAZ` (padrão) — nulidade processual + cadeia de custódia, escrita
  fria/cirúrgica/demolidora
- `MODO ADAYLDO` — prequestionamento (Súmula 212/STJ)
- `MODO PATRICK` — superação de Súmula 691 (urgência/teratologia)
- `MANUS` — só esqueleto estratégico, refinamento humano

**Arquivos atachados:** KAKAY HC.pdf, ALEGAÇÕES FINAIS PIER.pdf, HC TOFIC
SUPREMO.pdf, Innocence Project Brasil RE, RESP DORINHA, RA BITAR, TORON HC
LAVA JATO, MEMORIAL MÁRCIO TOMAS, BASE FUNDANTE_TRIAGEM, Upgrade do Kernel
Jurídico Avançado.

**Conformidade TIER 0:**

| Camada | Avaliação |
|---|---|
| C1 estilo | ✅ Vocabulário "Ruptura/Contaminação/Apócrifo" alinha com "Dado Líquido"; **⚠️ "vocabulário culto, mas agressivo"** está no limite da Camada 1 (não viola explicitamente "vocabulário que vira passivo", mas vale conferir se "agressivo" não desliza para metáfora vetada) |
| C3 verificação | ✅ "Protocolo Anti-Alucinação" — se faltar dado, PARA e pergunta — é exatamente o princípio raiz |
| C2 formato | ✅ Visual Law (tabelas Markdown) alinha com formato `petição-nexumdocs` |
| C4 auditor | ⚠️ Não declara auditor independente — depende do AUDITOR FORENSE para Camada 4 |
| C0 princípio raiz | ✅ "Você é o Marcelo Tigre" + handoff para curadoria humana |

**Recomendação:**
- **Manter** com revisão: substituir "agressivo" por "assertivo/incisivo"
  (não-passivo sem conotação ofensiva).
- **Portar para o engine:** os 4 modos (PERTINAZ/ADAYLDO/PATRICK/MANUS) podem
  virar parâmetro `modo_redacional` em `/draft/llm`, com prompt diferenciado.

---

## 2. `🕵️ Investigador Criminal - DEEP HUNTER (V13.0)` — VERIFICADOR (Camada 5)

**Função declarada:** Cyber-Archeology Edition. Mineração + cadeia de custódia
+ caça precedentes STJ/STF.

**Protocolo de ação (automático ao receber PDF/áudio/texto):**
1. Ciber-Arqueologia (hash, metadados, Art. 158-A CPP)
2. Auditoria de Silêncio (o que a polícia DEIXOU de juntar)
3. Jurisprudence Sniper (precedente exato)

**Output declarado:** `DOSSIÊ DE VULNERABILIDADES` + `JSON PAYLOAD` estruturado:
```json
{
  "INTEGRACAO_DRAFTER": {
    "MACRO_TESE_SUGERIDA": "NULIDADES_PROVA_DIGITAL",
    "MODO_ATUACAO_SUGERIDO": "PERTINAZ",
    "ESTRATEGIA_CENTRAL": "...",
    "COMANDOS_DRAFTER_ACIONAR": [1, 4, 7, 9, 42],
    "PRECEDENTES_ALVO_SUGERIDOS": ["STJ_QUEBRA_CADEIA_CUSTODIA_PRINTS"],
    "RED_FLAGS_ESTATAIS_IDENTIFICADAS": [...]
  }
}
```

**Modos:** CIBER-ARQUEÓLOGO / AUDITOR DE SILÊNCIO / CRONOS / SIMBIOSE.

**Conformidade TIER 0:**

| Camada | Avaliação |
|---|---|
| C3 verificação | ✅ Foco em hash/metadados/cadeia de custódia é a Camada 3 instrumentalizada |
| C0 princípio raiz | ✅ "Jamais escreva a peça" — respeita separação de poderes da Camada 4/5 |
| Termo problemático | ⚠️ **`Algorithmic Bypass`** como nome do mecanismo — internamente OK, mas em qualquer artefato exposto a juízo/cliente vira passivo retórico (sugere fraude). Renomear para "Pipeline de Auditoria Estruturada" ou similar |
| Premissa | ⚠️ "Presunção de NULIDADE da prova estatal" é mais agressivo que o princípio constitucional (que é presunção de INOCÊNCIA do réu). Útil internamente; **não** levar para peça |

**Recomendação:**
- **Manter** o gem como está (uso interno do curador).
- **Portar para o engine:** o **JSON PAYLOAD** vira schema de input expandido
  de `/draft/llm`. Engine pode aceitar `dossier_hunter: DossierIn` (com
  `red_flags`, `precedentes_alvo`, `macro_tese`) e injetar no prompt.
- **Não expor** os termos "Algorithmic Bypass" e "Presunção de Nulidade" em
  output cliente-facing.

---

## 3. `⇍AUDITOR FORENSE⇍` — AUDITOR (Camada 4 do TIER 0)

**Função declarada:** Auditor Advogado Sênior, postura clínica, fria,
matemática, 100% imparcial. Imune a vieses, retóricas, falácias.

**Metodologia de 5 passos:**
1. Micro-cronologia + cadeia de custódia (ID por ID)
2. Jurimetria/SLA — "Fenômeno dos 4 Minutos" (anomalia temporal =
   decisão pré-fabricada)
3. Metodologia da decisão + cegueira deliberada
4. Teorema do Contágio — árvore envenenada cross-processos
5. Relatório de materialidade + Lawfare Institucional

**Conformidade TIER 0:**

| Camada | Avaliação |
|---|---|
| C4 auditor adversarial | ✅ Cumpre EXATAMENTE o mandato — "**derrubar**" a peça/decisão; sem elogio próprio |
| C3 verificação | ✅ "Cegueira Seletiva Documental" mapeia para Camada 3.2 (premissa de fato) |
| C0 princípio raiz | ✅ "Imune a vieses" + foco em evidências rastreáveis (IDs) |

**Recomendação:**
- **Manter como ouro.** Este gem é o melhor alinhado de todos com TIER 0.
- **Portar para o engine:** o protocolo de 5 passos vira uma nova função
  `engine/src/nexus/auditor.py` que recebe a `minuta` + `feito` e devolve
  um parecer estruturado (REPROVA / APROVA PARA CURADORIA com ressalvas).
  Hoje o engine tem `quality_score` que é parcial — não cobre cegueira
  deliberada, anomalia temporal, contágio entre processos.

---

## 4. `M Advogado Criminalista amplificado By Tigre` — ESTRATEGISTA (Camada 5)

**Função declarada:** Inteligência jurídica de elite, garantista, técnica,
combativa. PADRÃO MARCELO TIGRE.

**Catálogo de conhecimento (13 JSONs temáticos):**
```
00-Metodologia | 01-Júri | 02-HC | 03-Recursos | 04-Provas | 05-Garantias
06-Execução | 07-Crimes | 08-Prisões | 09-Inteligência | 10-Peças Modelo
11-Violência Doméstica | 12-Profiling
```

**Travas explícitas:**
- **NUNCA:** Inventar jurisprudência | Afirmações sem fundamentação |
  Linguagem coloquial | Ignorar contexto | Teses inviáveis
- **SEMPRE:** Verificar atualidade | Mudanças legislativas | Adaptar ao caso |
  Priorizar interesse cliente | Ética profissional

**Conformidade TIER 0:**

| Camada | Avaliação |
|---|---|
| C0 princípio raiz | ✅ "NUNCA inventar jurisprudência" = exatamente HALT do engine |
| C3 verificação | ✅ "Verificar atualidade + mudanças legislativas" cobre Camada 3.1 |
| Catálogo | ✅ 13 áreas mapeadas = **fonte de verdade para `peca_tipo` enum** |

**Recomendação:**
- **Manter** como referência doutrinária do ESTRATEGISTA.
- **Portar para o engine:**
  - `peca_tipo` enum expandido (escopo §13 já previa: HC, RHC, RCL, APELACAO,
    MEMORIAIS, RESPOSTA_ACUSACAO, EDCL, AGRG, MANIFESTACAO)
  - Catálogo de "áreas" como tags do Audit row para query/relatório
  - As 13 JSONs temáticos parecem ser arquivos de RAG; vale auditar
    individualmente se forem alimentar o prompt do engine

---

## 5. `R - Ribeiro & Tigre - O Analista Primário` — VERIFICADOR (Camada 5)

**Função declarada:** Auditor Processual "Dissector". Postura clínica.

**Protocolo de 4 etapas:**
1. **Isolamento da Base Fática** (Fato Nu — sem qualificação adjetiva)
2. **Rastreamento da Origem** (Traceability) — com IDs PJe/e-SAJ/e-Proc
3. **Teste de Legitimidade STJ/STF** (Tema 280, HC 598.886, RHC 158.580,
   Art. 158-A CPP)
4. **Classificação:** 🟢 MOLDURA DE LIQUIDEZ vs 🔴 MOLDURA DE DUALIDADE

**Output template:** `RELATÓRIO DE DISSECAÇÃO PENAL` com Ementa + Análise
Rastreabilidade (FATO/Origem/Status/Análise) + Quadro de Molduras + Conclusão.

**Conformidade TIER 0:**

| Camada | Avaliação |
|---|---|
| C3.2 premissa de fato | ✅ "Fato Nu" sem adjetivação = Camada 3.2 |
| C3.6 proveniência | ✅ "Citação OBRIGATÓRIA da localização exata (PJe/e-SAJ/e-Proc)" |
| C0 princípio raiz | ✅ "Não defende nem acusa, audita" — pré-redação |

**Recomendação:**
- **Manter como ouro.** É o melhor template de output verificável que vi.
- **Portar para o engine:** o **template `RELATÓRIO DE DISSECAÇÃO PENAL`**
  vira o **Romaneio de Revisão** que projetei na auditoria anterior. Endpoint
  `GET /user/audits/{id}/romaneio` deveria produzir esse formato exato (com
  classificação `LIQUIDEZ`/`DUALIDADE` por fato).

---

## 6. `PERÍCIAS DIGITAIS` — apoio técnico

Pequeno (1.5 KB). Direciona análise de cadeia de custódia em 10 etapas (do
recolhimento até a obtenção), referenciando **RHC 143.169/RJ** (precedente
não-catalogado no engine).

**Recomendação:** adicionar `RHC 143.169/RJ` à base de precedentes de cadeia
de custódia digital catalogados em `engine/src/nexus/casos/data.py` (quando
houver caso que use).

## 7. `Engenharia Reversa` — código Python

**Não é prompt** — é **código Python** (`ChainOfCustodyAuditor`) que computa
SHA-256 + metadata do arquivo. **Conceitualmente idêntico ao que
`engine/src/nexus/upload.py` já faz no engine**.

**Recomendação:** o engine já cumpre essa função e em arquitetura melhor
(async + isolamento por user_id + validação de MIME + hash streaming). O
gem fica como referência conceitual; **engine implementa.**

## 8. `🕵️ PROJETO BEATRIZ TIGRE` (PAS/UnB) — FORA DO ESCOPO

Tutor de Direito para PAS/Cebraspe. Nada a ver com Nexus.

**Recomendação:** ignorar para fins do engine. Não auditar mais.

---

## Skills (`.skill` = zip ZIP files)

### `engenharia-juridica.skill` (8.5 KB) — a mais completa

Estrutura interna:
```
SKILL.md                      (9.6 KB — instrução principal)
scripts/organizar_drive.py    (11.6 KB — script de organização)
references/mapa_precedentes.md (6.9 KB — mapa STF/STJ)
templates/peticao_padrao.md   (2.6 KB — template peça)
references/, scripts/, templates/ (subdirs)
```

**Recomendação:** vale **extrair** o conteúdo do `SKILL.md` + `mapa_precedentes.md`
+ `peticao_padrao.md` (não fiz nesta auditoria; oferece dado novo para o engine).

### `peticao-nexumdocs.skill` (2.2 KB)

Estrutura mais enxuta. SKILL.md de ~7 KB. Referenciado por TIER 0 §1 como o
**formato canônico de petição** (corpo Times 12pt, margens 3cm/2cm, timbrado
institucional R&T, estrutura endereçamento → qualificação → nome → exórdio →
seções → requerimentos → fecho → assinatura).

**Recomendação:** alinhar os templates Jinja2 do engine (`hc.md.j2` e futuros)
ao formato `peticao-nexumdocs`. Pode ser via Pandoc-templating depois de o
texto gerado.

### `metodo-tigre.skill` (2.2 KB)

Estrutura mínima. Provável metodologia operacional. SKILL.md ~7 KB.

**Recomendação:** extrair e auditar separadamente. Se for o método dos
4 modos (Pertinaz/Adayldo/Patrick/Manus), confirma o que já vimos no
Redator de Elite.

---

## Síntese — o que o ECOSSISTEMA real faz vs. engine atual

| Função TIER 0 | Onde está hoje | Cobertura engine |
|---|---|---|
| ESTRATEGISTA (tese) | M Advogado Criminalista (Gem) | ❌ |
| VERIFICADOR + HUNTER (Dossiê + JSON Payload) | DEEP HUNTER + Analista Primário (Gems) | parcial — Dado Líquido só |
| REDATOR (4 modos) | Redator de Elite (Gem) | parcial — sem modos |
| AUDITOR (Camada 4) | AUDITOR FORENSE (Gem) | parcial — só quality_score |
| Romaneio de Revisão | ROMANEIO DE REVISAO (Drive doc) + Analista Primário template | ❌ |
| Persistência + cadeia de custódia | Engenharia Reversa (Python no Gem) | ✅ engine cobre melhor |
| Catálogo doutrinário | M Advogado JSONs temáticos | ❌ |

## Plano de portagem para o engine (ordem de prioridade)

1. **`peca_tipo` enum expandido** (do M Advogado catálogo) — 5 min de código
2. **`modo_redacional` em `/draft/llm`** (PERTINAZ/ADAYLDO/PATRICK/MANUS — do
   Redator de Elite) — 15 min
3. **Schema de input expandido** aceitando `dossier_hunter` (red_flags +
   macro_tese + precedentes_alvo — do DEEP HUNTER JSON) — 30 min
4. **Endpoint `GET /user/audits/{id}/romaneio`** produzindo o RELATÓRIO DE
   DISSECAÇÃO PENAL no formato do Analista Primário — 1h
5. **`engine/src/nexus/auditor.py`** implementando os 5 passos do AUDITOR
   FORENSE (anomalia temporal, cegueira deliberada, contágio inter-pecas) — 2h
6. **Extrair conteúdo dos 3 `.skill`** (especialmente `engenharia-juridica`)
   e incorporar `references/mapa_precedentes.md` e `templates/peticao_padrao.md`
   ao engine — 1h depois de extrair

Quando você quiser, eu sigo por esses pontos. Nada disso é urgente para o
deploy; é refinamento doutrinal para o produto estar 100% alinhado ao que
você JÁ pratica operacionalmente.
