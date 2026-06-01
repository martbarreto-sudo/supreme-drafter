# Skills (assets) extraídos do Drive

Estas são as 3 Skills (`.skill` = zip) que vivem no Drive de
`martbarreto@gmail.com`, descompactadas aqui para serem fonte da verdade
versionada e auditável no repo. Cada uma tem um `SKILL.md` com metadados YAML
+ instrução principal, opcionalmente acompanhada de `scripts/`, `references/`,
`templates/`.

Conexão com o protocolo TIER 0 (`docs/tier-0-protocolo.md`):

| Skill | Papel TIER 0 |
|---|---|
| `engenharia-juridica` | Cruzamento temático-fatual (Camada 1 — Dado Líquido) |
| `metodo-tigre` | Método dos 5 fases (= **Método Tigre V2.0** = Inova by Tigre) — Camadas 1-5 |
| `peticao-nexumdocs` | Formato canônico PJe (Camada 2) — referenciado em TIER 0 §C2 |

## `engenharia-juridica`

Sistema de **cruzamento temático-fatual** com taxonomia de 3 níveis:

```
Nivel 1: Macro-Teses        NULIDADES/, PRISAO_CAUTELAR/, PROVAS_DIGITAIS/...
Nivel 2: Precedentes        HC_598051_BUSCA_SEM_MANDADO/, HC_612234_HASH/...
Nivel 3: Dados Líquidos     CASO_PATRICK_XAVIER_LAUDO.pdf, etc.
```

Princípio: nunca cita tese abstrata sem Dado Líquido do caso concreto.
**Imperativo da Concreção** = exatamente o princípio raiz TIER 0 §0.

Conteúdo extraído:
- `SKILL.md` — instrução + taxonomia
- `scripts/organizar_drive.py` — automação Google Drive API
- `references/mapa_precedentes.md` — mapa de precedentes STF/STJ
- `templates/peticao_padrao.md` — template-âncora

## `metodo-tigre` — **= Método Tigre V2.0 = Inova by Tigre**

Sistema de análise criminal em **5 fases** com **REGRA CARDINAL: proibida
redação imediata**. Fases 1-4 são entregues primeiro como relatório; Fase 5
(produção da peça) só inicia após comando explícito *"Aprovado, siga para
a peça"*.

| Fase | Conteúdo | Entregável |
|---|---|---|
| 1 | Scanner Forense (auditoria reversa, micro-cronologia, isolamento mente jurisdicional) | Relatório cronológico com IDs, datas, atores, fissuras |
| 2 | Mapeamento de Teses (nulidades absolutas/relativas, mérito, cautelar, processual) | Lista rankeada com prob. êxito + tribunal-alvo |
| 3 | Estratégia de Destruição (tese líder, sequência silogística, precedentes com Dado Líquido, Visual Law) | Plano de ataque |
| 4 | Validação e Aprovação | AGUARDAR "Aprovado, siga para a peça" |
| 5 | Produção da Peça Final | Peça processual |

Esta skill **é** a Inova by Tigre operacionalizada em prompt — metodologia
autoral do Marcelo Tigre, independente do engine Nexus (este repo). A
correspondência com o ciclo TIER 0 ESTRATEGISTA → REDATOR → VERIFICADOR →
AUDITOR → CURADORIA HUMANA é a mesma cadeia de papéis, em vocabulário
ligeiramente diferente.

## `peticao-nexumdocs`

Padrão NexumDocs de peça processual: formato canônico PJe (Times 12pt,
margens 3/2cm, sem timbrado/rodapé/numeração — PJe numera). Voz do Tigre:
"denodo e respeito de estilo", "sobremodo enviesada", "sofreguidão
acusatória", "orfandade probatória". Negrito como bisturi. Ironia controlada.

Estrutura obrigatória da peça:
1. Endereçamento (centralizado, caixa alta, negrito)
2. Dados do Processo
3. Preâmbulo
4. Corpo (seções numeradas em romano)
5. Pedidos
6. Fecho
7. Assinatura

## Sobre extensão e implementação no engine

- O template `peticao_padrao.md` da `engenharia-juridica` pode (e deve)
  ser portado para `engine/src/nexus/templates/peticao_padrao.md.j2` como
  formato canônico Jinja2.
- O `mapa_precedentes.md` pode virar fonte de catálogo de precedentes
  citáveis (alimentando `engine/src/nexus/casos/data.py` ou um módulo
  dedicado de precedentes).
- O `organizar_drive.py` é utilitário operacional — fica como referência
  externa, sem porte para o engine (que opera localmente em
  `$CASO_DATA_DIR`, não no Drive).
- O **Método Tigre V2.0** (metodologia 5 fases) é a fonte conceitual do
  fluxo TIER 0 que já está implementado no engine (HALT + Dado Líquido +
  quality_score + auditor adversarial + Audit row). **Engine não substitui
  método**; engine é uma das *implementações* possíveis do método.
