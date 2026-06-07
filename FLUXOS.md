# Supreme Drafter V18 - Fluxos de Producao

## Arquitetura de Rotas NEXUM API v2

### Tier 1: Autenticacao e Sessao

```
POST /api/v2/auth/revoke
├── Middleware: mTLS + Admin Certificate
├── Funcao: DLP Kill-Switch (revoga sessao em <1s)
└── Redis: Invalida chave no cache de sessoes ativas
```

### Tier 2: Workspaces Isolados

```
POST /api/v2/workspaces
├── Middleware: JWT rt_nx_auth + RLS
├── Funcao: Criar workspace com tenant_id injetado
└── Banco: Row-Level Security impede cross-tenant

GET /api/v2/workspaces/{id}
├── Middleware: JWT + Tenant Check
├── Funcao: Recuperar metadados do workspace
└── Seguranca: IDOR silencioso em tentativa de acesso externo
```

### Tier 3: Upload e Ingestao

```
POST /api/v2/uploads/presign
├── Middleware: SHA-256 validado por scrubber.rs
├── Funcao: Gera URL assinada para S3 privado
└── Bucket: nexum-elite-private (AWS)

POST /api/v2/sources
├── Middleware: ClamAV + Unicode NFC
├── Funcao: Ingestao e indexacao de fontes PJe
└── Container: Triagem isolada antes de indexar
```

### Tier 4: RAG e Streaming

```
POST /api/v2/conversations
├── Middleware: context_lock = isolamento Gemini
├── Funcao: Inicializa consulta ao RAG
└── Validacao: Propriedade de cada source_id

GET /api/v2/messages/stream
├── Middleware: mTLS + Volatile RAM
├── Funcao: SSE streaming do Analista STJ
└── Purge: Buffers limpos apos encerramento
```

---

## Fluxo de Producao de Minutas

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FLUXO DE PRODUCAO V18                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. INGESTAO          2. SCRUBBER         3. GENS                   │
│  ┌─────────┐          ┌─────────┐         ┌─────────┐               │
│  │  PJe    │ ──────▶  │  Rust   │ ──────▶ │Custodia │               │
│  │ e-STJ   │          │scrubber │         │Reconhec.│               │
│  │ e-STF   │          │  .rs    │         │Chronos  │               │
│  └─────────┘          └─────────┘         └─────────┘               │
│       │                    │                   │                    │
│       │ PDF bruto          │ PII removido      │ Nulidades          │
│       │ .dylib sign        │ Unicode NFC       │ identificadas      │
│       │                    │ Hash SHA-256      │                    │
│       ▼                    ▼                   ▼                    │
│  ┌─────────────────────────────────────────────────────┐            │
│  │               4. GERACAO DE MINUTA                  │            │
│  │         Supreme Drafter Engine (Claude)             │            │
│  └─────────────────────────────────────────────────────┘            │
│                            │                                        │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────┐            │
│  │               5. CURADORIA HUMANA                   │            │
│  │         CuradoriaProtocolo.tsx (MacBook)            │            │
│  └─────────────────────────────────────────────────────┘            │
│                            │                                        │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────┐            │
│  │               6. PROTOCOLO PJe                      │            │
│  │         Token OAB (PKCS#11) + mTLS                  │            │
│  └─────────────────────────────────────────────────────┘            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Workspaces Ativos

| WS | Nome | Casos | Status |
|----|------|-------|--------|
| I | Operacao Kefale | Osnir, Frederico, Francismary, Regival | Pendente |
| II | Prescricao | Leandro Ferreira | URGENTE (31/03/2027) |
| III | Hearsay Rule | Leandro Vidal, Raphael Lopes | Entregue/Pendente |
| IV | Consuncao | Henrique de Moraes | Analise |
| V | Execucao Penal | Brunno de Sena | Analise |
| VI | Medidas Protetivas | Felipe Barbalho | Pendente |

---

## Gens (Agentes Inteligentes)

### Gen-Custodia
- **Escopo**: Art. 158-A e 158-B CPP
- **Funcao**: Valida hash, metadados e cadeia de custodia digital
- **Alerta**: `METADATA_SOURCE_NOT_FOUND` se faltar hash de origem

### Gen-Reconhecimento
- **Escopo**: Art. 226 CPP / HC 598.887/SC / Lei 13.869/19
- **Funcao**: Identifica reconhecimentos indutivos e abuso de autoridade
- **Alerta**: Interrogatorio sem defensor = nulidade absoluta

### Gen-Chronos
- **Escopo**: Art. 109 CP / Art. 315 CPP
- **Funcao**: Calcula prescricao e monitora prazos fatais
- **Alerta**: Countdown ativo para termos prescricionais

---

## Entregas Concluidas

| Data | Caso | Arquivo | Tamanho |
|------|------|---------|---------|
| 04/06/2026 | Leandro Vidal | REsp_Leandro_Vidal_Art155_Hearsay.pdf | 41 KB |
| 04/06/2026 | Joao Marcos | REsp_Joao_Marcos_Inclusao_Federal.pdf | 42 KB |

---

## Proximos na Fila

1. **Leandro Ferreira** - Prescricao intercorrente (URGENTE)
2. **Frederico Xavier** - Abuso de autoridade Art. 13, III
3. **Raphael Lopes** - Impronuncia hearsay
4. **Henrique de Moraes** - Consuncao + 9mm uso restrito
5. **Osnir Cabeca** - Cadeia de custodia Bambam
6. **Brunno de Sena** - Falta grave sem apreensao

---

## Infraestrutura

### Cloudflare Edge
- Subdominio: `ai.ribeiroetigre.org`
- Protecao: mTLS obrigatorio
- Fallback: HTTP 444 (conexao silenciosa)

### AWS S3
- Bucket: `rt-soberano-carol-aws-s3`
- Object Lock: Modo conformidade 365 dias
- Imutabilidade: Art. 158-A CPP

### Local-First (Tauri/Rust)
- Keyring: macOS Keychain (.dylib)
- Scrubber: RAM-only, purge imediato
- mTLS: PKCS#12 (client.p12)
