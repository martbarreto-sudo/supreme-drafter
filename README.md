# Deep Hunter × Supreme Drafter

Ecossistema de **Doutrina de Combate Híbrido** — dois agentes autónomos e segregados
que auditam a prova digital dos autos e convertem as vulnerabilidades detectadas em
peças processuais de alto teor persuasivo.

A segregação cognitiva é deliberada: o auditor **nunca** redige a peça final e o
redator **nunca** inventa factos. O elo entre eles é um contrato de dados rígido
(JSON), de modo a eliminar o risco de alucinação jurídica.

```
┌────────────────────┐        Dossiê + Tabela de        ┌────────────────────┐
│  AGENTE 01          │        Nulidades (JSON)          │  AGENTE 02          │
│  Deep Hunter        │ ───────────────────────────────▶ │  Supreme Drafter    │
│  (o Auditor)        │                                  │  (o Executor)       │
│  cético · forense   │                                  │  retórico · agressivo│
└────────────────────┘                                  └────────────────────┘
         ▲                                                        │
         │ autos (PDF)                                            ▼
    Operador Tier 0 ◀──────── revisão · validação · assinatura ── peça (Markdown)
```

## Componentes

| Componente | Papel | Perfil |
|---|---|---|
| **Agente 01 — Deep Hunter** | Perito forense de computação sénior. Processa os autos em PDF, audita metadados, mapeia cronologias e confronta a cadeia de custódia. Popula o contrato único **`DossierHunterSchema`** (linha do tempo, auditoria de juiz natural, custódia, filtros de omissão). | Cético, frio, técnico. Nunca redige a peça. |
| **Agente 02 — Supreme Drafter** | Converte os factos líquidos auditados em memoriais, recursos e ordens de Habeas Corpus. Proibido de pesquisar factos novos. | Retórico, agressivo, elevada cultura jurídica. |
| **Operador Tier 0** | O advogado. Revisão final, formatação, validação das teses e assinatura. | Humano. |

## Modos de investigação (Deep Hunter)

| Modo | Foco |
|---|---|
| `CRONOS` | Cronologia dos factos e lapsos temporais na cadeia de custódia. |
| `FORENSE` | Metadados, IPs, chaves *hash* e laudos periciais. Desconsidera depoimentos orais. |
| `POLIGRAFO` | Confronto de contradições entre depoimentos (fase policial × instrução judicial). |
| `SIMBIOSE` | Varredura padrão: Cadeia de Custódia + Competência + Contemporaneidade. |

## Comandos de auditoria (Deep Hunter)

| Comando | Verificação |
|---|---|
| `HASH_AUDIT` | Valida as assinaturas criptográficas dos arquivos digitais (princípio da *mesmidade*). |
| `WRITE_BLOCKER` | Audita o uso de bloqueadores físicos de escrita na extração (Cellebrite/IPED). |
| `CLOUD_EXTRACTION` | Identifica acesso remoto não autorizado a nuvem (WhatsApp Web / iCloud). |

## Arquitetura de contratos (Mapeamento Agnóstico — Opção B)

Os contratos de dados nascem blindados contra falhas de tipagem (Pydantic v2),
antes de qualquer amarração de rede ou banco relacional:

| Módulo | Papel |
|---|---|
| `schema/dossier_hunter.py` | Contrato do **Módulo Hunter** — `DossierHunterSchema` (cronologia PJe, auditoria de juiz natural, cadeia de custódia, filtros de omissão imputáveis ao Estado). Valida NPU no padrão CNJ. |
| `core/draft_engine.py` | **Módulo Drafter** — `DraftEngine` + `ModoRedacional` (`PERTINAZ`, `PREQUESTIONADOR`, `CUSTODIA`, `NULIDADE`). Compõe a diretriz retórica sob *Temperatura Zero Invariante*, sem tocar no system prompt (cache hits). O acoplamento com o Hunter dá-se por `DraftRequest.dados_hunter`. |

O pacote `deep_hunter/` (abaixo) é a **camada de transporte** que fala com a API
Claude; os módulos `schema/` e `core/` são a **camada de contrato + retórica**.

## 📋 Checklist de Ingestão e Produção (HITL — Tier 0)

1. **Injeção de variáveis**: `ANTHROPIC_API_KEY` (e `GCP_WIF` para revisores paralelos, se aplicável).
2. **Abstração por schemas**: toda entrada telemática passa obrigatoriamente pela validação de `schema/dossier_hunter.py`.
3. **Modos redacionais**: o endpoint `/draft/llm` aceita as flags `PERTINAZ`, `PREQUESTIONADOR`, `CUSTODIA`, `NULIDADE`; entradas divergentes → HTTP 422.

## Instalação

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # e preencha ANTHROPIC_API_KEY
```

### Suíte de testes (Zero-Credencial, isolada de rede)

```bash
pytest        # ou: pytest tests/
```

## Uso

```bash
# Auditoria + redação, saída em ./out/
python -m deep_hunter run autos.pdf --modo SIMBIOSE --modo-redacional CUSTODIA

# Apenas a auditoria (JSON do DossierHunterSchema)
python -m deep_hunter audit autos.pdf --modo FORENSE --comando HASH_AUDIT

# Apenas a redação, a partir de um dossiê já auditado
python -m deep_hunter draft dossie.json --modo-redacional NULIDADE
```

> Sem instalar (`pip install -e .`), exporte `PYTHONPATH=src:.` — o pacote `deep_hunter`
> vive em `src/` e os contratos `schema`/`core` no topo do repo.

Via Python:

```python
from deep_hunter import Pipeline, Modo, ModoRedacional

pipeline = Pipeline()
resultado = pipeline.run("autos.pdf", modo=Modo.SIMBIOSE, modo_redacional=ModoRedacional.CUSTODIA)
print(resultado.dossie.npu)          # DossierHunterSchema validado
print(resultado.peca_markdown)
```

## Gateway declarativo — `POST /draft/llm`

O barramento síncrono valida o corpo nativamente (Pydantic) e devolve **HTTP 422** se o
NPU ou o payload falharem na tipagem — antes de qualquer composição.

```
[Request] ─► POST /draft/llm ─► Validação nativa Pydantic ─► 422 (falha)
                                          │
                                          ▼ (payload íntegro)
                            DraftEngine.compor_instrucao_retorica
```

```bash
pip install "uvicorn>=0.29"
PYTHONPATH=src:. uvicorn deep_hunter.api:app --reload
```

Rotas:

| Rota | Descrição |
|---|---|
| `POST /audit` | Recebe os autos em PDF (`multipart/form-data`, campo `file`) e devolve o `DossierHunterSchema` (auditor **mock local**, Zero-Credencial). PDF vazio/corrompido → **422**; acima do teto de upload (~25 MB, o que cabe em 32 MB depois do base64) → **413**. |
| `POST /draft/llm` | Recebe `{modo, conteudo_base, dados_hunter: DossierHunterSchema}` e devolve a instrução retórica. Payload espúrio → **422** nativo. |
| `GET /health` | Sonda de saúde. |

### Ciclo local completo (Zero-Credencial)

```
PDF bruto ─► POST /audit ─► DossierHunterSchema ─► POST /draft/llm ─► instrução/minuta
```

> `POST /audit` opera em **modo simulação**: extrai texto do PDF e gera um dossiê
> determinístico (semeado pelo hash do conteúdo), com omissões intencionais derivadas
> dos termos encontrados (`hash`, `plenário`, `portaria`, `contemporaneidade`). Não é
> perícia real — ligue o `DeepHunter` real quando houver credencial.

### Extração de texto (`deep_hunter/pdf_text.py`)

A varredura de termos lê o **texto efectivamente exibido** na página, não os bytes
crus do ficheiro. O extractor é stdlib pura (sem dependências, sem rede): localiza os
*content streams*, infla o que for deflate (`zlib`) e interpreta os operadores de
exibição (`Tj`, `TJ`, `'`, `"`), remontando palavras partidas por kerning dentro dos
vectores `TJ`. A normalização remove acentos, de modo que `plenário ≡ plenario`.

Ordem de tentativa — vence a primeira que render texto:

| Ordem | Via | Quando actua |
|---|---|---|
| 1 | Extractor stdlib | Padrão. Cobre o PDF comprimido típico do PJe. |
| 2 | `pypdf` | Só se instalado **e** se (1) nada render — fica opcional para que a instalação padrão permaneça determinística. |
| 3 | Varredura crua `latin-1` | Resgate para PDFs sem streams (lineares, não comprimidos). |

> ⚠️ Por que isto importa: enquanto a varredura era feita sobre os bytes crus, todo
> PDF real (texto dentro de stream comprimido) era lido como **vazio** — e portanto
> auditado como "seco", com todas as omissões sinalizadas e a cadeia de custódia dada
> por quebrada mesmo quando os autos traziam hash, ata e portaria. Num instrumento
> forense esse é o pior modo de falha: **fabricar nulidades inexistentes**.

Limites assumidos (é best-effort, não um parser PDF completo): não resolve `/Length`
indirecto, não decifra PDFs encriptados e não aplica `/Differences` de codificação de
fonte. Para perícia real, `pypdf`/`pdfplumber` continuam a ser o caminho.

## Canal do modelo — primeira parte ou Vertex AI

O motor fala, por omissão, com a **API comercial da Anthropic**. Quem exija que os
autos não saiam do seu próprio perímetro de nuvem comuta para o **Vertex AI**, onde
o Claude é servido dentro do projecto Google Cloud do cliente, por variável de
ambiente — sem alterar uma linha do pipeline:

```bash
DEEP_HUNTER_PROVEDOR=vertex
ANTHROPIC_VERTEX_PROJECT_ID=meu-projecto-gcp
CLOUD_ML_REGION=us-east5          # a região define onde a inferência ocorre
```

As credenciais do Vertex resolvem-se por ADC (`gcloud auth application-default
login`); um provedor desconhecido é recusado na construção do `RunConfig`, e a rota
Vertex sem as dependências instaladas falha com indicação do extra
(`pip install "anthropic[vertex]"`).

Tudo o que o Deep Hunter exige do canal é suportado nas duas rotas: PDF como bloco
`document`, saída estruturada, *adaptive thinking* com `effort` e streaming. O que
**não** é portável: `inference_geo` (residência de dados por parâmetro) existe
apenas na API de primeira parte — no Vertex a localização da inferência é a região
do projecto. A disponibilidade do modelo fixado em `DEEP_HUNTER_MODEL` numa dada
região do Vertex é facto do catálogo do provedor, a confirmar por quem opera.

## Nota técnica sobre determinismo

A especificação pede *temperatura zero*. O modelo `claude-opus-4-8` não aceita o
parâmetro `temperature` (retorna 400). O objectivo — respostas determinísticas e
ancoradas — é alcançado por:

- `output_config={"effort": "high"}` e *adaptive thinking* (raciocínio controlado);
- um **contrato de grounding** no system prompt que obriga a ancorar cada entrada no
  `id_documento` do PJe que a comprova (citação de página fica indisponível: as
  citações nativas da API são incompatíveis com `output_config.format` — daí
  `load_pdf_block(..., citations=False)` no Deep Hunter);
- **saída estruturada nativa** para o Deep Hunter: o contrato vai como
  `output_format=DossierHunterSchema` e é o SDK que deriva o JSON Schema estrito
  (`output_config.format`) e valida a resposta — o bloco de texto volta com
  `parsed_output` já tipado. Não há conversor próprio a manter: as restrições que a
  API não aceita como palavra-chave (o `pattern` do NPU) seguem anexadas à
  `description` pelo próprio SDK, e a validação usa `TypeAdapter.validate_json`,
  pelo que um NPU fora do padrão CNJ continua a ser recusado;
- `DEEP_HUNTER_EFFORT` validado na construção do `RunConfig` (`low`…`max`), em vez de
  falhar no servidor a meio de uma auditoria.

> ⚠️ Ferramenta de apoio à investigação defensiva (Provimento 188/2018 CFOAB). Toda a
> saída é minuta sujeita à revisão e assinatura do Operador Tier 0. Não constitui
> aconselhamento jurídico.
