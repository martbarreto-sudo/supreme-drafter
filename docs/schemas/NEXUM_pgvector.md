# NEXUM — Camada de normalizacao pgvector (busca semantica / RAG)

Documento de regras da camada `nexum/engine/`. GREENFIELD: entrega o **nucleo de
normalizacao vetorial + schema + recuperacao**. NAO entrega as rotas HTTP nem o
embedder real (ver secao "O que NAO esta implementado").

## Por que L2-normalize na escrita + cosseno + HNSW

- **L2-normalize na escrita** (`nexum/engine/vectors.py::l2_normalize`): todo
  embedding vira vetor unitario (norma == 1) antes de ir ao banco. Com vetores
  unitarios vale a identidade

  ```
  cosine_distance(a, b) == 1 - dot(a, b)
  ```

  que e exatamente o que o operador `<=>` (`vector_cosine_ops`) do pgvector
  computa. Normalizar na escrita torna a busca estavel e permite tratar o
  produto interno como proxy direto da similaridade.
- **Regra do vetor zero**: um vetor de norma nula nao tem direcao definida.
  `l2_normalize` levanta `ValueError` em vez de dividir por zero ou devolver
  zeros (o que corromperia silenciosamente o ranking).
- **Cosseno** e a metrica natural para embeddings de texto (invariante a escala,
  sensivel a direcao semantica).
- **HNSW** (`idx_chunks_embedding_hnsw ... USING hnsw (embedding vector_cosine_ops)`)
  da busca aproximada de vizinho-mais-proximo com boa latencia/recall, casando
  com o operador `<=>` usado na query.

Referencia Python pura (sem numpy) em `vectors.py`: `cosine_distance`,
`cosine_similarity` — usadas nos testes e como fallback sem banco.

## Dimensao do embedding (configuravel)

- Default **768**, lido de `NEXUM_EMBEDDING_DIM` por `vectors.py::EMBEDDING_DIM`.
- O literal `vector(768)` em `nexum/engine/schema.sql` e o **default commitado** e
  DEVE casar com a env. SQL nao le variaveis de ambiente: **mudar a dimensao
  exige regenerar o DDL** (trocar 768 nos dois literais `vector(...)`) e reindexar.
- Divergencia entre a dim do embedder e a coluna causa erro de INSERT.

## Politica de chunking (`nexum/engine/chunking.py`)

- Janelas de **~512 tokens** (`target_tokens`) com **12% de sobreposicao**
  (`overlap_ratio=0.12`), respeitando fronteiras de paragrafo/sentenca (uma
  unidade nunca e partida ao meio).
- **Contagem de tokens por espacos em branco** como PROXY — um tokenizer real
  (tiktoken/sentencepiece) substituiria `_count_tokens` sem mudar o fluxo.
- **Preservacao de `fls.`**: extrai a primeira referencia de folha (`fls. N`) por
  regex, conforme a doutrina Deep Hunter de rastreabilidade probatoria. Vai para
  a coluna `chunks.fls_ref`.
- Deterministico, sem rede. `chunk_index` (campo `index`) monotonico a partir de 0.

## Fluxo /sources -> chunks -> embeddings -> retrieval

Mapeado sobre as rotas de `docs/api-spec.json` (as rotas em si sao o proximo
passo; aqui esta o nucleo que elas orquestrariam):

1. **`POST /sources`** (payload `s3_key`, `workspace_id`, `source_type` in
   `[peticao,decisao,acordao,laudo,midia]`, `metadata{npu,tribunal,data_documento}`)
   -> linha em `sources` (`status='queued'`, `clamav_result`).
2. Extracao do texto -> **`chunk_text`** -> lista de `Chunk`
   (`index, content, fls_ref, token_count`).
3. **`Embedder.embed`** gera um vetor por chunk (dim = `EMBEDDING_DIM`).
4. **`retrieval.upsert_chunks`** L2-normaliza cada embedding e faz upsert
   idempotente em `chunks` (`ON CONFLICT (source_id, chunk_index) DO UPDATE`).
   `source.status` avancaria para `indexed`.
5. **`POST /conversations`** (`workspace_id`, `source_ids`, `context_lock`) fixa o
   escopo; **`GET /messages/stream`** embeda o `prompt` e chama
   **`retrieval.search`** (`SEARCH_SQL`: KNN por `<=>`, filtro `workspace_id`,
   `similarity = 1 - distancia`), streamando os trechos recuperados via SSE.

## Isolamento de tenant (RLS)

`workspace_id` e denormalizado em `chunks` para filtro por tenant sem JOIN na
busca. As politicas RLS (`ENABLE ROW LEVEL SECURITY` + `CREATE POLICY ... USING
(workspace_id = current_setting('nexum.workspace_id')::uuid)`) estao documentadas
como comentario em `schema.sql` mas **nao habilitadas** neste greenfield; enquanto
isso, `search` sempre filtra por `workspace_id` no `WHERE`.

## Embedder (`nexum/engine/embeddings.py`)

- `Embedder` Protocol: `embed(texts) -> list[list[float]]`.
- `DeterministicFakeEmbedder`: deriva cada posicao de `sha256(f"{text}#{i}")`,
  L2-normaliza. Mesmo texto -> mesmo vetor; sem rede/relogio/aleatoriedade —
  testes de recuperacao 100% deterministicos.
- `build_embedder_from_env`: default `fake`; `gemini`/`vertex` sao importacao
  LAZY que hoje levanta `NotImplementedError("wire Gemini/Vertex here")`.

## Infra para pgvector real

- `docker-compose.yml` e `.github/workflows/nexum-ci.yml` usam
  **`pgvector/pgvector:pg16`** (superset drop-in do `postgres:16`). O compose
  monta `nexum/engine/schema.sql` como `02-engine.sql` (apos `01-outbox.sql`).
- `nexum/engine/integration_test.py` (`@pytest.mark.integration`) conecta via
  `NEXUM_OUTBOX_DSN`, cria a extensao (skip se indisponivel), faz upsert de 2
  chunks e valida ordenacao nearest-first. Faz SKIP limpo sem DB/extensao.

## O que NAO esta implementado (honestidade de escopo)

Este PR entrega o **nucleo de normalizacao vetorial + schema + recuperacao**.
Ainda NAO fazem parte:

- As rotas FastAPI **`/sources`, `/conversations`, `/messages/stream`** (HTTP/SSE).
- O **embedder real** (Gemini/Vertex) — hoje apenas o fake deterministico + stub.
- A pipeline de extracao de texto de PDFs/midia e a integracao ClamAV.
