# NEXUM V18 — Conhecimento Conglobado

## Matriz de Integração Sistêmica

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA CONGLOBADA NEXUM V18                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   CAMADA JURÍDICA              CAMADA TÉCNICA           CAMADA OPERACIONAL │
│   ┌─────────────┐              ┌─────────────┐          ┌─────────────┐     │
│   │ 6 Workspaces│◄────────────►│ 7 API Routes│◄────────►│ 3 Gens IA   │     │
│   │ 148 NPUs    │              │ 4 Tiers     │          │ HITL Layer  │     │
│   │ 12 Teses    │              │ mTLS/RLS    │          │ Chronos     │     │
│   └─────────────┘              └─────────────┘          └─────────────┘     │
│         │                            │                        │             │
│         └────────────────────────────┼────────────────────────┘             │
│                                      │                                      │
│                              ┌───────▼───────┐                              │
│                              │ SUPREME       │                              │
│                              │ DRAFTER       │                              │
│                              │ ENGINE        │                              │
│                              └───────────────┘                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## I. Taxonomia de Teses Jurídicas

### Cluster 1: Prova Ilícita e Cadeia de Custódia

| Tese | Fundamento Legal | Gen Responsável | Precedente Paradigma |
|------|------------------|-----------------|---------------------|
| Quebra de Cadeia de Custódia Digital | Arts. 158-A e 158-B CPP | Gen-Custódia | HC 1.036.370/PR |
| Ausência de Hash Criptográfico | ABNT NBR ISO/IEC 27037:2013 | Gen-Custódia | — |
| Extração sem Laudo UFED/Cellebrite | Art. 159 CPP | Gen-Custódia | — |
| Metadados Ausentes | Art. 158-B, IV, CPP | Gen-Custódia | — |

**Parágrafo de Ouro — Custódia:**
> "A ausência de documentação técnica da cadeia de custódia (hash SHA-256, logs de extração, termo de apreensão) torna a prova digital irrefutável no mau sentido: impossível verificar adulterações. A prova não confrontável viola o devido processo constitucional."

### Cluster 2: Hearsay e Elementos Inquisitoriais

| Tese | Fundamento Legal | Gen Responsável | Precedente Paradigma |
|------|------------------|-----------------|---------------------|
| Condenação por Hearsay | Art. 155 CPP | — | REsp 1.916.733/MG |
| Pronúncia por Testemunho Indireto | Art. 155 CPP + Art. 414 CPP | — | Tema 1.260/STJ |
| Elementos Inquisitoriais Exclusivos | Art. 155 CPP | — | AgRg no RHC 186.044/CE |
| Violação ao Direito de Confronto | Art. 8.2.f CADH + Art. 212 CPP | — | — |

**Parágrafo de Ouro — Hearsay:**
> "O testemunho de 'ouvir dizer' padece de vício estrutural: não permite o confronto. O declarante originário jamais comparece ao crivo da defesa. A condenação ou pronúncia fundada exclusivamente em hearsay viola o critério legal de valoração da prova."

### Cluster 3: Reconhecimento e Abuso de Autoridade

| Tese | Fundamento Legal | Gen Responsável | Precedente Paradigma |
|------|------------------|-----------------|---------------------|
| Reconhecimento Fotográfico Indutivo | Art. 226 CPP | Gen-Reconhecimento | HC 598.887/SC |
| Interrogatório sem Defensor | Art. 13, III, Lei 13.869/19 | Gen-Reconhecimento | — |
| Show-Up (Apresentação Individual) | Art. 226, II, CPP | Gen-Reconhecimento | HC 712.781/RJ |
| Lineup sem Pessoas Semelhantes | Art. 226, II, CPP | Gen-Reconhecimento | — |

**Parágrafo de Ouro — Reconhecimento:**
> "O reconhecimento pessoal que não observa o rito do Art. 226 do CPP — especialmente a exigência de colocação do suspeito entre outras pessoas semelhantes — constitui prova irrepetível viciada, impondo-se seu desentranhamento."

### Cluster 4: Interceptação Telefônica e Competência

| Tese | Fundamento Legal | Gen Responsável | Precedente Paradigma |
|------|------------------|-----------------|---------------------|
| Prorrogações sem Fundamentação | Art. 93, IX, CF + Tema 661/STF | — | RE 625.263/PR |
| Usurpação de Competência (Foro) | Art. 102, I, "b", CF | — | Pet 3.825/MT |
| Encontro Fortuito Simulado | Art. 102, I, "b", CF | — | Rcl 7.913 AgR |
| Ação Controlada Clandestina | Lei 12.850/13 | — | — |

**Parágrafo de Ouro — Interceptação:**
> "O 'despacho-padrão' que se limita a estampar 'J. Defiro' ou 'Ante a necessidade, prorrogo' é a confissão judicial da ausência de controle estrito sobre a flexibilização de direitos fundamentais. Viola o Tema 661/STF."

### Cluster 5: Prescrição e Execução Penal

| Tese | Fundamento Legal | Gen Responsável | Precedente Paradigma |
|------|------------------|-----------------|---------------------|
| Prescrição Intercorrente PPP | Art. 109 CP + Art. 110 CP | Gen-Chronos | — |
| Prescrição Virtual/Antecipada | Art. 109 CP | Gen-Chronos | Súmula 438/STJ |
| Contemporaneidade para SPF | Art. 10, §1º, Lei 11.671/08 | Gen-Chronos | Súmula 661/STJ |
| Falta Grave sem Apreensão Física | Art. 57 LEP | Gen-Chronos | — |

**Parágrafo de Ouro — Prescrição:**
> "A prescrição é matéria de ordem pública, cognoscível de ofício. O Gen-Chronos monitora termos fatais e emite alertas quando o decurso do prazo prescricional se aproxima, priorizando casos com countdown ativo."

### Cluster 6: Fundamentação e Due Process

| Tese | Fundamento Legal | Gen Responsável | Precedente Paradigma |
|------|------------------|-----------------|---------------------|
| Fundamentação Per Relationem Abstrata | Art. 315, §2º, CPP | — | REsp 2.072.790/DF |
| In Dubio Pro Societate Inconstitucional | Art. 5º, LVII, CF | — | ARE 1.067.392/CE |
| Omissão sobre Contraprovas | Art. 315, §2º, III e IV, CPP | — | — |
| Motivação Genérica de Prisão | Art. 315 CPP | — | — |

---

## II. Mapeamento de Rotas por Função Jurídica

### Matriz Rota × Tese

| Rota API | Função Processual | Teses Servidas |
|----------|-------------------|----------------|
| `/auth/revoke` | DLP Kill-Switch | Sigilo profissional, dados sensíveis |
| `/workspaces` | Isolamento por Caso | RLS, IDOR, multi-tenancy |
| `/uploads/presign` | Ingestão de Autos | Cadeia de custódia, hash SHA-256 |
| `/sources` | Indexação de Fontes | Art. 158-A CPP, metadados |
| `/conversations` | Consulta RAG | Context lock, isolamento de contexto |
| `/messages/stream` | Streaming SSE | Geração de minutas, HITL |

### Fluxo de Dados por Tese

```
[TESE: Cadeia de Custódia]
    │
    ├── /uploads/presign ─► SHA-256 validado por scrubber.rs
    │
    ├── /sources ─► Gen-Custódia verifica metadados
    │       │
    │       └── ALERTA: METADATA_SOURCE_NOT_FOUND
    │
    └── /conversations ─► Minuta com argumento de nulidade
            │
            └── context_lock: true (fontes locais apenas)

[TESE: Hearsay/Art. 155]
    │
    ├── /sources ─► Indexa depoimentos (tipo: "decisao", "acordao")
    │
    ├── /conversations ─► Analisa natureza da prova
    │       │
    │       └── Identifica: (a) inquisitorial, (b) hearsay, (c) direta
    │
    └── /messages/stream ─► Gera REsp com distinguishing

[TESE: Prescrição]
    │
    ├── /sources ─► Extrai datas (fato, recebimento, trânsito)
    │
    ├── Gen-Chronos ─► Calcula termo prescricional
    │       │
    │       └── ALERTA: PRESCRIPTION_WARNING (300 dias)
    │
    └── Dashboard ─► Countdown timer ativo
```

---

## III. Workspaces: Cartografia Processual

### Workspace I: Operação Kéfale

| Caso | NPU | Tese Principal | Status | Prazo |
|------|-----|----------------|--------|-------|
| Osnir Cabeça | 0002237-43.2025.8.17.2730 | Cadeia de Custódia (Bambam) | Pendente | — |
| Frederico Xavier | 0002237-43.2025.8.17.2730 | Abuso Art. 13, III | Pendente | — |
| Francismary | — | — | Pendente | — |
| Regival | — | — | Pendente | — |

**Conexão Jurídica:** Celular de "Bambam" sem hash MD5/SHA-256 → litispendência → nulidade por cadeia de custódia.

### Workspace II: Prescrição

| Caso | NPU | Tese Principal | Status | Prazo |
|------|-----|----------------|--------|-------|
| Leandro Ferreira | AP 0031951-54.2006.8.17.0001 | Prescrição PPP 12 anos | **URGENTE** | 31/03/2027 |

**Countdown Ativo:** 300 dias para termo fatal.

### Workspace III: Hearsay Rule

| Caso | NPU | Tese Principal | Status | Prazo |
|------|-----|----------------|--------|-------|
| Leandro Vidal | RSE 0018084-07.2026.8.17.2001 | Art. 155 CPP / Tema 1.260 | **ENTREGUE** | — |
| Raphael Lopes | AP 0015384-69.2024.8.17.2990 | Impronúncia hearsay | Pendente | — |

**Entrega:** `REsp_Leandro_Vidal_Art155_Hearsay.pdf` (41 KB)

### Workspace IV: Consunção

| Caso | NPU | Tese Principal | Status | Prazo |
|------|-----|----------------|--------|-------|
| Henrique de Moraes | RHC 232.619/PE | Consunção + 9mm uso restrito | Análise | — |

**Tese:** Pistola 9mm é de uso RESTRITO (não proibido) → afastamento da hediondez.

### Workspace V: Execução Penal

| Caso | NPU | Tese Principal | Status | Prazo |
|------|-----|----------------|--------|-------|
| Brunno de Sena | GEP 1002725-87.2021.8.17.4001 | Falta grave sem apreensão | Análise | — |

**Tese:** Inércia judicial em escolta não configura falta grave imputável ao apenado.

### Workspace VI: Medidas Protetivas

| Caso | NPU | Tese Principal | Status | Prazo |
|------|-----|----------------|--------|-------|
| Felipe Barbalho | — | — | Pendente | — |

---

## IV. Gens: Especificação Técnica

### Gen-Custódia

```yaml
nome: Gen-Custódia
versão: 1.0.0
escopo_legal:
  - Art. 158-A CPP (definição de cadeia de custódia)
  - Art. 158-B CPP (etapas do rastreamento)
  - ABNT NBR ISO/IEC 27037:2013 (evidência digital)

inputs:
  - laudo_pericial.pdf
  - extração_celular.bin
  - termo_apreensão.pdf

outputs:
  - validação_hash: boolean
  - metadados_presentes: boolean
  - alerta: METADATA_SOURCE_NOT_FOUND | HASH_MISMATCH | CUSTODY_BREAK

regras:
  - SE ausente(hash_sha256) ENTÃO alerta(METADATA_SOURCE_NOT_FOUND)
  - SE ausente(termo_apreensão) ENTÃO alerta(CUSTODY_BREAK)
  - SE hash_informado != hash_calculado ENTÃO alerta(HASH_MISMATCH)
```

### Gen-Reconhecimento

```yaml
nome: Gen-Reconhecimento
versão: 1.0.0
escopo_legal:
  - Art. 226 CPP (formalidades do reconhecimento)
  - HC 598.887/SC (STJ, 6ª Turma)
  - Lei 13.869/19 (abuso de autoridade)

inputs:
  - auto_reconhecimento.pdf
  - depoimento_testemunha.pdf
  - termo_interrogatório.pdf

outputs:
  - rito_observado: boolean
  - lineup_válido: boolean
  - defensor_presente: boolean
  - alerta: PHOTO_LINEUP_VIOLATION | COUNSEL_ABSENT | SHOWUP_DETECTED

regras:
  - SE reconhecimento_fotográfico AND NOT lineup_6_pessoas ENTÃO alerta(PHOTO_LINEUP_VIOLATION)
  - SE interrogatório AND NOT defensor_presente ENTÃO alerta(COUNSEL_ABSENT)
  - SE apresentação_individual ENTÃO alerta(SHOWUP_DETECTED)
```

### Gen-Chronos

```yaml
nome: Gen-Chronos
versão: 1.0.0
escopo_legal:
  - Art. 109 CP (prazos prescricionais)
  - Art. 110 CP (prescrição retroativa)
  - Art. 315 CPP (fundamentação de decisões)
  - Art. 10, §1º, Lei 11.671/08 (contemporaneidade SPF)

inputs:
  - denúncia.pdf (data do fato, recebimento)
  - sentença.pdf (pena aplicada)
  - trânsito_em_julgado.pdf

outputs:
  - termo_prescricional: date
  - dias_restantes: integer
  - alerta: PRESCRIPTION_WARNING | PRESCRIPTION_IMMINENT | PRESCRIPTION_OCCURRED

regras:
  - SE dias_restantes < 365 ENTÃO alerta(PRESCRIPTION_WARNING)
  - SE dias_restantes < 90 ENTÃO alerta(PRESCRIPTION_IMMINENT)
  - SE dias_restantes <= 0 ENTÃO alerta(PRESCRIPTION_OCCURRED)

dashboard:
  - countdown_timer: ativo
  - priorização_automática: por proximidade do termo
```

---

## V. Protocolo de Operação HITL

### Checklist de Curadoria

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROTOCOLO DE CURADORIA V18                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [ ] 1. VERIFICAR ALERTAS DO GEN-CHRONOS                        │
│      └─ Priorizar casos com countdown < 90 dias                 │
│                                                                 │
│  [ ] 2. VALIDAR FUNDAMENTAÇÃO FÁTICA                            │
│      └─ Cada afirmação tem lastro documental?                   │
│      └─ Citações de páginas/IDs corretas?                       │
│                                                                 │
│  [ ] 3. CONFERIR TESES JURÍDICAS                                │
│      └─ Precedentes citados existem?                            │
│      └─ Súmulas aplicáveis estão atualizadas?                   │
│      └─ Distinguishing necessário?                              │
│                                                                 │
│  [ ] 4. AUDITAR CADEIA DE CUSTÓDIA                              │
│      └─ Se prova digital: hash presente?                        │
│      └─ Se extração: laudo UFED anexado?                        │
│                                                                 │
│  [ ] 5. VERIFICAR FORMATAÇÃO                                    │
│      └─ NPU no padrão CNJ?                                      │
│      └─ Citações em fonte reduzida?                             │
│      └─ Assinatura e OAB preenchidos?                           │
│                                                                 │
│  [ ] 6. DECISÃO                                                 │
│      ├─ APROVAR → Protocolo automático PJe                      │
│      └─ REJEITAR → Devolver com motivo                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Fluxo de Rejeição

```
[MINUTA REJEITADA]
    │
    ├── Motivo: [ ] Erro de fato
    │            [ ] Precedente desatualizado
    │            [ ] Formatação incorreta
    │            [ ] Cadeia de custódia não explorada
    │            [ ] Tese insuficiente
    │
    ├── Comentário: _________________________________
    │
    └── Retorno ao Stage 4 (Geração de Minuta)
            │
            └── Claude/Gemini recebe feedback → Regera
```

---

## VI. Métricas de Qualidade

### KPIs Operacionais

| Métrica | Meta | Frequência | Responsável |
|---------|------|------------|-------------|
| Tempo médio de curadoria | < 30 min/minuta | Diário | Operador |
| Taxa de rejeição | < 15% | Semanal | CEO |
| Casos com prazo < 30 dias pendentes | 0 | Diário | Gen-Chronos |
| Fila de curadoria ao fim do dia | < 10 itens | Diário | Operador |
| Alertas de Gen ignorados | 0 | Semanal | Auditoria |

### Dashboard de Saúde

```
┌─────────────────────────────────────────────────────────────────┐
│                    HEALTH CHECK NEXUM V18                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  API STATUS                                                     │
│  ├── /auth/revoke ............ [●] ONLINE (mTLS + AdminCert)   │
│  ├── /workspaces ............. [●] ONLINE (JWT + RLS)          │
│  ├── /uploads/presign ........ [●] ONLINE (SHA-256)            │
│  ├── /sources ................ [●] ONLINE (ClamAV)             │
│  ├── /conversations .......... [●] ONLINE (context_lock)       │
│  └── /messages/stream ........ [●] ONLINE (SSE)                │
│                                                                 │
│  GENS STATUS                                                    │
│  ├── Gen-Custódia ............ [●] ATIVO (0 alertas pendentes) │
│  ├── Gen-Reconhecimento ...... [●] ATIVO (0 alertas pendentes) │
│  └── Gen-Chronos ............. [●] ATIVO (1 countdown ativo)   │
│                                                                 │
│  WORKSPACES                                                     │
│  ├── I  Kéfale ............... 4 casos | Pendente              │
│  ├── II Prescrição ........... 1 caso  | URGENTE (300d)        │
│  ├── III Hearsay ............. 2 casos | 1 Entregue            │
│  ├── IV Consunção ............ 1 caso  | Análise               │
│  ├── V  Execução Penal ....... 1 caso  | Análise               │
│  └── VI Medidas Protetivas ... 1 caso  | Pendente              │
│                                                                 │
│  ENTREGAS HOJE: 3 PDFs (Vidal, João Marcos, Diagnóstico Tigre) │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## VII. Infraestrutura de Segurança

### Modelo de Ameaças

| Ameaça | Mitigação | Camada |
|--------|-----------|--------|
| Interceptação de dados em trânsito | mTLS obrigatório (PKCS#12) | Tier 2 |
| Acesso cross-tenant | Row-Level Security (RLS) | Tier 2 |
| Adulteração de provas digitais | Object Lock 365 dias (S3) | Tier 3 |
| Exfiltração de dados sensíveis | DLP Kill-Switch (< 1s) | Tier 1 |
| Prompt injection | Context lock + validação de fonte | Tier 4 |
| IDOR em workspaces | Tenant check + UUID não sequencial | Tier 2 |

### Matriz de Certificados

| Certificado | Tipo | Uso | Validade |
|-------------|------|-----|----------|
| client.p12 | PKCS#12 | mTLS cliente | 1 ano |
| admin.p12 | PKCS#12 | Kill-Switch | 6 meses |
| oab_token.p11 | PKCS#11 | Protocolo PJe | Conforme OAB |

---

## VIII. Entregas Realizadas

| Data | Caso | Arquivo | Tamanho | Tese Principal |
|------|------|---------|---------|----------------|
| 04/06/2026 | Leandro Vidal | REsp_Leandro_Vidal_Art155_Hearsay.pdf | 41 KB | Art. 155 CPP / Tema 1.260 |
| 04/06/2026 | João Marcos | REsp_Joao_Marcos_Inclusao_Federal.pdf | 42 KB | Cadeia Custódia / Súmula 661 |
| 07/06/2026 | Diagnóstico Tigre | REsp_Diagnostico_Tigre_Usurpacao_Competencia.pdf | 46 KB | Art. 102 CF / Tema 661 STF |

---

## IX. Próximas Ações

### Fila Priorizada

1. **[URGENTE]** Leandro Ferreira — Prescrição (300 dias para termo fatal)
2. Frederico Xavier — Abuso de autoridade Art. 13, III
3. Raphael Lopes — Impronúncia hearsay
4. Henrique de Moraes — Consunção + 9mm
5. Osnir Cabeça — Cadeia de custódia Bambam
6. Brunno de Sena — Falta grave sem apreensão

### Temas Jurídicos Pendentes de Monitoramento

| Tema | Tribunal | Status | Impacto |
|------|----------|--------|---------|
| Tema 1.260 | STJ | Vista Min. Schietti | Alto (Hearsay/Pronúncia) |
| Tema 661 | STF | Fixado | Alto (Interceptação) |

---

*Documento gerado pelo Supreme Drafter V18 — NEXUM Platform*
*Ribeiro & Tigre Advogados — Confidencial*
*Data: 9 de junho de 2026*
