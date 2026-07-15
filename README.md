# Supreme Drafter V18 — Ribeiro & Tigre

Plataforma NEXUM de produção de minutas penais assistida por IA (Gen-Custódia, Gen-Reconhecimento, Gen-Chronos).

## Estrutura do Repositório

```
.
├── index.html              # Landing / acesso ao Terminal Tier 0
├── docker-compose.yml      # Stack dev: postgres + redis + pub/sub + consumer + relay
├── Makefile                # up / down / logs / test / test-integration / psql
├── minutas/                # Peças jurídicas produzidas
│   ├── html/               # Fontes HTML editáveis
│   └── pdf/                # Entregas finais (protocoláveis)
├── nexum/                  # Pipeline forense CloudEvents v1.0 (Tier 0)
│   ├── infra/              # schema.sql (outbox + seeds) + smoke_test.py
│   └── Dockerfile          # Imagem única (consumer via uvicorn / relay via -m)
├── deploy/                 # Chart Helm K8s (consumer + relay; stores externos)
├── docs/                   # Documentação da plataforma
│   ├── FLUXOS.md           # Fluxos de produção + rotas API v2
│   ├── NEXUM_CONGLOBADO_V18.md / .pdf
│   ├── dashboard.html + Supreme_Drafter_V18_Dashboard.pdf
│   ├── manual-joao-felipe.html + Manual_Joao_Felipe_NEXUM_V18.pdf
│   └── api-spec.json       # Especificação NEXUM API v2
└── .github/                # CI (claude-integration workflow)
```

Para rodar o pipeline NEXUM localmente (Postgres + Redis + emulador Pub/Sub),
veja [`nexum/README.md`](nexum/README.md#rodar-localmente-docker-compose) (`make up`).

## Minutas Entregues

| Caso | Peça | Tese central | Arquivo |
|------|------|--------------|---------|
| Leandro Vidal | REsp | Hearsay / Art. 155 CPP | `minutas/pdf/REsp_Leandro_Vidal_Art155_Hearsay.pdf` |
| João Marcos | REsp | Inclusão em presídio federal | `minutas/pdf/REsp_Joao_Marcos_Inclusao_Federal.pdf` |
| Diagnóstico Tigre | REsp | Usurpação de competência STF | `minutas/pdf/REsp_Diagnostico_Tigre_Usurpacao_Competencia.pdf` |
| Leandro Ferreira | REsp | Prescrição intercorrente (URGENTE) | `minutas/pdf/REsp_Leandro_Ferreira_Prescricao_Intercorrente.pdf` |
| Frederico Xavier | REsp | Abuso de autoridade — Art. 13, III, Lei 13.869/19 | `minutas/pdf/REsp_Frederico_Xavier_Abuso_Autoridade.pdf` |
| Geovane | REsp | Falta grave / PAD nulo — Súmula 533 STJ | `minutas/pdf/REsp_Geovane_Falta_Grave_PAD.pdf` |
| Raphael Lopes | REsp | Impronúncia hearsay — Tema 1.260/STJ | `minutas/pdf/REsp_Raphael_Lopes_Impronuncia_Hearsay.pdf` |
| Henrique de Moraes | RHC | Consunção + afastamento hediondez (9mm) | `minutas/pdf/RHC_Henrique_Moraes_Consuncao_9mm.pdf` |
| Osnir Cabeça | REsp | Cadeia de custódia — Op. Kéfale | `minutas/pdf/REsp_Osnir_Cabeca_Cadeia_Custodia.pdf` |
| Brunno de Sena | Agravo | Falta grave sem apreensão física | `minutas/pdf/Agravo_Brunno_Sena_Falta_Grave.pdf` |

**Backlog Trello: ZERADO.**

## Gerar PDF a partir do HTML

```bash
python3 -c "from weasyprint import HTML; HTML('minutas/html/<peca>.html').write_pdf('minutas/pdf/<Peca>.pdf')"
```

## Referência

Detalhes de arquitetura, workspaces, Gens e infraestrutura em [`docs/FLUXOS.md`](docs/FLUXOS.md) e [`docs/NEXUM_CONGLOBADO_V18.md`](docs/NEXUM_CONGLOBADO_V18.md).
