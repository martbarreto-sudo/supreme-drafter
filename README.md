# Supreme Drafter V18 — Ribeiro & Tigre

Plataforma NEXUM de produção de minutas penais assistida por IA (Gen-Custódia, Gen-Reconhecimento, Gen-Chronos).

## Estrutura do Repositório

```
.
├── index.html              # Landing / acesso ao Terminal Tier 0
├── minutas/                # Peças jurídicas produzidas
│   ├── html/               # Fontes HTML editáveis
│   └── pdf/                # Entregas finais (protocoláveis)
├── docs/                   # Documentação da plataforma
│   ├── FLUXOS.md           # Fluxos de produção + rotas API v2
│   ├── NEXUM_CONGLOBADO_V18.md / .pdf
│   ├── dashboard.html + Supreme_Drafter_V18_Dashboard.pdf
│   ├── manual-joao-felipe.html + Manual_Joao_Felipe_NEXUM_V18.pdf
│   └── api-spec.json       # Especificação NEXUM API v2
└── .github/                # CI (claude-integration workflow)
```

## Minutas Entregues

| Caso | Peça | Tese central | Arquivo |
|------|------|--------------|---------|
| [NOME_OMITIDO] | REsp | Hearsay / Art. 155 CPP | `minutas/pdf/[PECA_OMITIDA]` |
| [NOME_OMITIDO] | REsp | Inclusão em presídio federal | `minutas/pdf/[PECA_OMITIDA]` |
| Diagnóstico Tigre | REsp | Usurpação de competência STF | `minutas/pdf/[PECA_OMITIDA]` |
| [NOME_OMITIDO] | REsp | Prescrição intercorrente (URGENTE) | `minutas/pdf/[PECA_OMITIDA]` |
| [NOME_OMITIDO] | REsp | Abuso de autoridade — Art. 13, III, Lei 13.869/19 | `minutas/pdf/[PECA_OMITIDA]` |
| [NOME_OMITIDO] | REsp | Falta grave / PAD nulo — Súmula 533 STJ | `minutas/pdf/[PECA_OMITIDA]` |
| [NOME_OMITIDO] | REsp | Impronúncia hearsay — Tema 1.260/STJ | `minutas/pdf/[PECA_OMITIDA]` |
| [NOME_OMITIDO] | RHC | Consunção + afastamento hediondez (9mm) | `minutas/pdf/[PECA_OMITIDA]` |
| [NOME_OMITIDO] | REsp | Cadeia de custódia — [OPERACAO_OMITIDA] | `minutas/pdf/[PECA_OMITIDA]` |
| [NOME_OMITIDO] | Agravo | Falta grave sem apreensão física | `minutas/pdf/[PECA_OMITIDA]` |

**Backlog Trello: ZERADO.**

## Gerar PDF a partir do HTML

```bash
python3 -c "from weasyprint import HTML; HTML('minutas/html/<peca>.html').write_pdf('minutas/pdf/<Peca>.pdf')"
```

## Referência

Detalhes de arquitetura, workspaces, Gens e infraestrutura em [`docs/FLUXOS.md`](docs/FLUXOS.md) e [`docs/NEXUM_CONGLOBADO_V18.md`](docs/NEXUM_CONGLOBADO_V18.md).
