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
| **Agente 01 — Deep Hunter** | Perito forense de computação sénior. Processa os autos em PDF, audita metadados, mapeia cronologias e confronta a cadeia de custódia. Emite um *Dossiê de Vulnerabilidades* e uma *Tabela de Nulidades*. | Cético, frio, técnico. Nunca redige a peça. |
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

## Instalação

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # e preencha ANTHROPIC_API_KEY
```

## Uso

```bash
# Auditoria + redação, saída em ./out/
python -m deep_hunter run autos.pdf --modo SIMBIOSE --peca habeas_corpus

# Apenas a auditoria (JSON com Dossiê + Tabela de Nulidades)
python -m deep_hunter audit autos.pdf --modo FORENSE --comando HASH_AUDIT

# Apenas a redação, a partir de um dossiê já auditado
python -m deep_hunter draft dossie.json --peca memorial
```

Via Python:

```python
from deep_hunter import Pipeline

pipeline = Pipeline()
resultado = pipeline.run("autos.pdf", modo="SIMBIOSE", peca="habeas_corpus")
print(resultado.peca_markdown)
```

## Nota técnica sobre determinismo

A especificação pede *temperatura zero*. O modelo `claude-opus-4-8` não aceita o
parâmetro `temperature` (retorna 400). O objectivo — respostas determinísticas e
ancoradas — é alcançado por:

- `output_config={"effort": "high"}` e *adaptive thinking* (raciocínio controlado);
- um **contrato de grounding** no system prompt que obriga à citação da folha (`fls.`)
  dos autos para validar qualquer facto;
- **saída estruturada** (`output_config.format`) para o Deep Hunter, garantindo um
  payload JSON estável entregue ao Supreme Drafter.

> ⚠️ Ferramenta de apoio à investigação defensiva (Provimento 188/2018 CFOAB). Toda a
> saída é minuta sujeita à revisão e assinatura do Operador Tier 0. Não constitui
> aconselhamento jurídico.
