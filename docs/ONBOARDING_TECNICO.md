# Deep Hunter × Supreme Drafter — Manual de Onboarding Técnico

Destinatário: equipa de engenharia que assume a operação do motor. Pressupõe
Python ≥ 3.10 e nenhum conhecimento prévio do domínio jurídico.

Tudo neste documento é verificável sem credenciais: a suíte corre isolada de rede.
Comece por aí — é o caminho mais curto para confiar no resto.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest                      # 58 testes, sem rede, sem chaves
```

Se os 58 passarem, o contrato de dados, o gateway, a extracção de PDF e a
comutação de canal estão íntegros nesta máquina.

---

## 1. O que o sistema é, em dois parágrafos

Dois agentes **segregados por desenho**. O **Deep Hunter** audita os autos digitais
em PDF e popula um contrato de dados tipado; o **Supreme Drafter** converte esse
contrato numa peça processual. O auditor nunca redige; o redator nunca pesquisa
factos. O único elo entre eles é o contrato JSON — e é essa separação que elimina a
alucinação: o redator não tem como afirmar o que o contrato não contém.

A saída **nunca é um acto processual**. É minuta sujeita a revisão e assinatura do
advogado (o "Operador Tier 0"). Qualquer alteração que enfraqueça esse pressuposto
muda a natureza jurídica do produto — trate-o como invariante, não como detalhe.

## 2. Mapa do código

| Caminho | Papel |
|---|---|
| `schema/dossier_hunter.py` | **O contrato.** `DossierHunterSchema` (Pydantic v2): cronologia de actos PJe, auditoria de juiz natural, cadeia de custódia, sinalizadores de omissão. Valida NPU no padrão CNJ. É a fonte única de verdade — tudo o mais deriva daqui. |
| `core/draft_engine.py` | Diretrizes retóricas por `ModoRedacional`. Compõe a instrução sem tocar no *system prompt* (preserva *cache hits*). |
| `src/deep_hunter/agents.py` | Os dois agentes. O auditor usa saída estruturada nativa do SDK (`output_format=DossierHunterSchema`). |
| `src/deep_hunter/pipeline.py` | Orquestração `audit → draft`. Ponto de entrada programático. |
| `src/deep_hunter/providers.py` | Comutação de canal: API de primeira parte ou Vertex AI. |
| `src/deep_hunter/pdf_text.py` | Extracção de texto de PDF em stdlib pura (infla *content streams*, lê operadores de exibição). Sem dependências, sem rede. |
| `src/deep_hunter/mock_auditor.py` | Auditor local **em simulação**, para fechar o ciclo sem credenciais. Não é perícia. |
| `src/deep_hunter/api.py` | Gateway FastAPI: `/health`, `/audit`, `/draft/llm`. |
| `src/deep_hunter/cli.py` | `python -m deep_hunter audit|draft|run`. |

> Sem `pip install -e .`, exporte `PYTHONPATH=src:.` — o pacote vive em `src/` e os
> contratos em `schema/`/`core/`, no topo da árvore do serviço.

## 3. Operar

### Linha de comando

```bash
python -m deep_hunter run autos.pdf --modo SIMBIOSE --modo-redacional CUSTODIA
python -m deep_hunter audit autos.pdf --modo FORENSE --comando HASH_AUDIT
python -m deep_hunter draft dossie.json --modo-redacional NULIDADE
```

Saídas em `./out/` (`dossie.json`, `peca.md`); `--out` muda o directório.

### Gateway

```bash
PYTHONPATH=src:. uvicorn deep_hunter.api:app --reload
```

| Rota | Comportamento |
|---|---|
| `POST /audit` | PDF em `multipart/form-data` (campo `file`) → `DossierHunterSchema`. **Auditor mock**, zero credenciais. PDF vazio/corrompido → 422; acima de ~25 MB → 413. |
| `POST /draft/llm` | `{modo, conteudo_base, dados_hunter}` → instrução retórica. Payload fora do contrato → 422 nativo do Pydantic. |
| `GET /health` | Sonda. |

### Vocabulário de controlo

**Modos de investigação:** `CRONOS` (cronologia e lapsos), `FORENSE` (metadados,
IPs, hashes — ignora depoimentos), `POLIGRAFO` (contradições entre depoimentos),
`SIMBIOSE` (varredura padrão: custódia + competência + contemporaneidade).

**Comandos de auditoria:** `HASH_AUDIT` (mesmidade), `WRITE_BLOCKER` (bloqueador de
escrita na extracção), `CLOUD_EXTRACTION` (acesso remoto a nuvem).

**Modos redacionais:** `PERTINAZ` (equilíbrio), `PREQUESTIONADOR` (prepara recurso
às instâncias superiores), `CUSTODIA` (liberdade imediata no topo), `NULIDADE`
(micro-desconstrução vício a vício).

## 4. Configuração

| Variável | Efeito |
|---|---|
| `ANTHROPIC_API_KEY` | Credencial da rota de primeira parte. |
| `DEEP_HUNTER_MODEL` | Modelo (padrão `claude-opus-4-8`). **Lido no import** do pacote. |
| `DEEP_HUNTER_EFFORT` | `low`…`max` (padrão `high`). Valor inválido é recusado na construção do `RunConfig`, não no servidor. |
| `DEEP_HUNTER_PROVEDOR` | `anthropic` (padrão) ou `vertex`. **Lido na construção**, não no import. |
| `ANTHROPIC_VERTEX_PROJECT_ID`, `CLOUD_ML_REGION` | Rota Vertex. Credenciais por ADC (`gcloud auth application-default login`). A região determina onde a inferência ocorre. |

Rota Vertex exige `pip install "anthropic[vertex]"`; sem isso falha com indicação
do extra. Tudo o que o pipeline usa — PDF, saída estruturada, *adaptive thinking*
com `effort`, streaming — é GA nas duas rotas, pelo que a troca não altera código.

## 5. Decisões de desenho que não são acidentais

Mexer nestas sem perceber porquê quebra garantias que não aparecem nos testes.

**Temperatura.** A especificação pede determinismo, mas o modelo em uso não aceita
`temperature` (devolve 400). O determinismo é perseguido por `effort` + *adaptive
thinking* + contrato de *grounding* no *system prompt* + saída estruturada. Não
adicione `temperature`.

**Citações desligadas no auditor.** As citações nativas da API são incompatíveis com
saída estruturada (`output_config.format` → 400). Daí
`load_pdf_block(..., citations=False)`. O *grounding* é obtido exigindo que cada
entrada se ancore no `id_documento` do PJe — não na página.

**Saída estruturada é do SDK, não nossa.** `output_format=DossierHunterSchema`: o
SDK deriva o schema estrito, preserva na `description` as restrições que a API não
aceita como palavra-chave (o `pattern` do NPU) e valida a resposta com
`TypeAdapter.validate_json`. Houve um conversor próprio; foi aposentado porque
descartava o `pattern` em silêncio — e um NPU livre só era detectado depois de a
auditoria estar paga. Não reintroduza um conversor manual.

**Streaming obrigatório.** `max_tokens` é 32000; sem streaming a requisição atinge o
timeout HTTP do SDK.

**Defaults conservadores.** `possui_quebra_custodia` e
`omissao_analise_contemporaneidade` nascem `True`. Isto é doutrinário: o ónus de
integridade é da acusação. Consequência operacional a ter presente — **silêncio nos
autos converte-se em achado de nulidade**. É escolha, não defeito, mas quem opera
deve sabê-lo.

## 6. Limites conhecidos — o que não está feito

Declarados de propósito. Herdar um sistema sem esta lista é herdar surpresas.

1. **Gateway sem autenticação, sem rate limit, sem CORS.** Inofensivo em loopback
   zero-credencial; é o primeiro item a resolver antes de qualquer exposição.
2. **`cli.py` sem cobertura de testes** (56 linhas). Os ramos de recusa do modelo em
   `agents.py` também não são exercitados.
3. **NPU validado só na forma.** O dígito verificador do CNJ (módulo 97) não é
   conferido: `0000000-00.2026.8.17.0000` passa.
4. **`/audit` é simulação.** O auditor mock gera dossiê determinístico semeado pelo
   hash do conteúdo, com omissões derivadas de termos encontrados no texto. Ligar o
   `DeepHunter` real exige credencial.
5. **`pdf_text` é *best-effort*, não parser completo.** Não resolve `/Length`
   indirecto, não decifra PDFs encriptados, não aplica `/Differences` de codificação
   de fonte. Para perícia real, `pypdf`/`pdfplumber`.
6. **Retenção de dados é configuração de organização, não do código.** Nada neste
   repositório activa ou garante *Zero Data Retention*. Ver a cláusula de governança.

## 7. Primeiras 48 horas de quem assume

1. Corra `pytest`. 58 verdes = base sã.
2. Leia `schema/dossier_hunter.py` de ponta a ponta — 76 linhas que governam tudo.
3. Suba o gateway e faça o ciclo local: `POST /audit` com um PDF → o dossiê devolvido
   → `POST /draft/llm`. Sem credencial nenhuma.
4. Leia `tests/test_api_gateway.py`: é a especificação executável do gateway.
5. Só então ligue uma credencial e corra `python -m deep_hunter audit` sobre autos
   reais, comparando o dossiê com a sua própria leitura das peças.
6. Antes de expor o gateway, resolva o item 1 da secção 6.
