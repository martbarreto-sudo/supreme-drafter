# Hub de Agentes Inteligentes — Ecossistema Ribeiro & Tigre / Nexus

> Mapa consolidado do ecossistema: brand público, protocolo doutrinário,
> agentes (Gems), assets (Skills), engine (este repo) e como tudo se conecta
> em **uma cadeia única sob curadoria humana**. Fonte da verdade canônica.

## 1. Brand público (não-confundir com infra)

### 1.1. Ribeiro & Tigre Advocacia Criminal

- **Fundação:** 2009, por **Marcelo Tigre** e **Ydigoras Jr.** em Pernambuco.
- **Sede:** Recife/PE. **Filiais:** Brasília/DF, São Paulo/SP.
- **OAB do operador:** Marcelo Tigre, OAB/PE 27.543.
- **Track record:** 100+ defesas em Tribunal do Júri; ≥600 sustentações orais.
- **Áreas:** advocacia criminal estratégica, com equipe multi-disciplinar
  (criminologia, psicologia, perícias técnicas).
- **Compromisso pro bono:** violações de direitos humanos, vítimas de
  violência policial.
- **Serviço B2B:** consultoria para outras bancas (pareceres, memórias para
  defesas em diferentes instâncias).
- **Sites:** [ribeiroetigre.adv.br](https://ribeiroetigre.adv.br) (institucional
  da banca), [ribeiroetigre.org](https://ribeiroetigre.org) (espelho/landing
  tecnológica — onde mora o JSON-LD do JSON-LD do schema.org commit `867cc42`).
- **Instagram:** [@ribeiroetigre](https://www.instagram.com/ribeiroetigre/) e
  [@marcelo.tigre](https://www.instagram.com/marcelo.tigre/).

### 1.2. Inova by Tigre — produto público da metodologia

- **Autoria:** **Marcelo Tigre** — método desenvolvido por ele a partir da
  prática operacional consolidada do escritório (100+ júris, 600+ sustentações,
  atuação em STJ/STF). Diego Cavalcante atua na gestão/business e César Caputo
  na supervisão jurídica complementar; a metodologia em si é do Marcelo.
- **Tese:** **metodologia em 10 etapas**, da triagem inicial da ação criminal
  à checagem final da tese jurídica. Inspirada em **teoria dos jogos**
  aplicada ao processo penal — antecipa movimentos da acusação, mapeia
  padrões decisórios, propõe estratégias baseadas em dados reais.
- **Modelo comercial:** mentoria seletiva para advogados/bancas; plano de
  disponibilizar parte para defensores públicos gratuitamente.
- **Imprensa:**
  - ConJur, set/2025: [Inova by Tigre lança método com IA para reduzir falhas em defesas criminais](https://www.conjur.com.br/2025-set-05/inova-by-tigre-lanca-metodo-com-ia-para-reduzir-falhas-em-defesas-criminais/)
  - Metrópoles: [Inova by Tigre revoluciona defesa criminal](https://www.metropoles.com/conteudo-especial/inova-by-tigre-revoluciona-defesa-criminal-com-metodo-que-integra-ia)
  - GPS Brasília: [Metodologia revoluciona advocacia criminal ao unir IA e estratégia jurídica](https://gpsbrasilia.com.br/metodologia-revoluciona-advocacia-criminal-ao-unir-ia-e-estrategia-juridica/)
- **Site:** [inovabytigre.com](https://inovabytigre.com).

### 1.3. Nexus by Tigre — **infraestrutura técnica** deste repo

- **Não é produto público.** É a infra que executa o protocolo TIER 0 em
  software (este repo, branch `claude/laughing-sagan-rnQo1`, 26 commits +
  este = 27).
- **Stack:** Python 3.11 + FastAPI + SQLAlchemy async + Alembic + bcrypt +
  JWT + Stripe (para Fase comercial) + slowapi.
- **Status hoje:** auth + trial + Stripe + LGPD + rate limit + Dockerfile +
  railway.toml + 113/113 testes verdes.
- **Posicionamento:** se for público algum dia, é como **ferramenta de
  produtividade para advogados B2B** (escopo §1), não consultoria ao leigo.
- **Recomendação estratégica anterior** ([recomendacao-estrategica.md](./recomendacao-estrategica.md)):
  Nexus permanecer infra interna do escritório; Inova by Tigre é a marca
  comercial. Decisão depois revisada para "marketplace agora" e arquitetada
  em [marketplace-escopo.md](./marketplace-escopo.md).

## 2. Protocolo doutrinário — fonte da verdade

[tier-0-protocolo.md](./tier-0-protocolo.md) — 7 camadas. Resumindo o que
governa tudo:

| Camada | Função |
|---|---|
| 0 | Identidade + **princípio raiz**: nenhuma afirmação sem fonte primária lida |
| 1 | Estilo (Dado Líquido, FATO → PRECEDENTE → SUBSUNÇÃO) |
| 2 | Formato (padrão PJe via skill `peticao-nexumdocs`) |
| 3 | Verificação (VERIFICADO / NÃO-VERIFICADO / INFERIDO) |
| 4 | Auditor adversarial — separação de poderes (REDATOR ≠ AUDITOR) |
| 5 | Papéis: ESTRATEGISTA → REDATOR → VERIFICADOR → AUDITOR → **CURADORIA HUMANA** |
| 6 | Segurança e limites |
| 7 | Invocação operacional |

## 3. O hub de agentes — quem faz o quê

Mapa cruzado dos Gems Gemini ([audit-drive-gems.md](./audit-drive-gems.md))
com os papéis TIER 0 e os endpoints do engine:

```
┌──────────────────────────────────────────────────────────────────────┐
│                CURADOR HUMANO (Dr. Marcelo Tigre, OAB/PE 27.543)     │
│         decide · revisa · ajusta · assina · protocola · NUNCA pula   │
└──────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ minuta + romaneio + parecer adversarial
                              │
┌─────────────────────────────┴────────────────────────────────────────┐
│                   CICLO TIER 0 — engine Nexus                        │
│                                                                       │
│  [ESTRATEGISTA]  Gem: M Advogado Criminalista amplificado            │
│       │            Engine: POST /draft/llm (modo_redacional futuro)   │
│       ▼                                                               │
│  [HUNTER]        Gem: 🕵️ DEEP HUNTER V13.0 (Cyber-Archaeology)        │
│  [ANALISTA]      Gem: R - Analista Primário (Dissector)              │
│       │            Engine: POST /autos (hash:// fonte)                │
│       │                  + dossier_hunter JSON (a portar)            │
│       ▼                                                               │
│  [VERIFICADOR]   embutido no /draft/llm — HALT + Dado Líquido         │
│       │            Engine: assertions_falhas em response              │
│       ▼                                                               │
│  [REDATOR]       Gem: ⚖️ Redator de Elite (4 modos)                  │
│       │            Engine: gerar_minuta() em nexus/llm.py             │
│       │                  + disclaimer obrigatório                     │
│       ▼                                                               │
│  [AUDITOR]       Gem: ⇍AUDITOR FORENSE⇍ (5 passos)                   │
│       │            Engine: quality_score parcial; nexus/auditor.py    │
│       │                  com 5 passos é a próxima feature             │
│       ▼                                                               │
│  [PERSISTÊNCIA + AUDIT TRAIL]                                         │
│       Engine: Audit row + minuta em $CASO_DATA_DIR/{user_id}/...      │
│              GET /user/audits/{id} + GET /user/me/export (LGPD)       │
└──────────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────┴────────────────────────────────────────┐
│         CAMADA DE APOIO (não estão no ciclo principal)               │
│                                                                       │
│  Gem: PERÍCIAS DIGITAIS           → consultor de cadeia de custódia  │
│  Gem: Engenharia Reversa (Py)     → conceito; engine já implementa   │
│  Gem: 🕵️ Beatriz Tigre PAS/UnB    → fora do escopo Nexus             │
└──────────────────────────────────────────────────────────────────────┘
```

## 4. Assets do hub — as 3 Skills

| Skill | Tamanho | Função | Status engine |
|---|---|---|---|
| `engenharia-juridica.skill` | 8.5 KB | SKILL.md + scripts/organizar_drive.py + references/mapa_precedentes.md + templates/peticao_padrao.md | conteúdo a extrair e portar |
| `peticao-nexumdocs.skill` | 2.2 KB | Formato canônico de petição (Times 12pt, margens 3/2cm, timbrado R&T) — citado em TIER 0 §C2 | alinhar templates Jinja2 (`hc.md.j2`) |
| `metodo-tigre.skill` | 2.2 KB | Metodologia operacional (provável overlap com os 4 modos do Redator de Elite) | confirmar conteúdo |

## 5. Repositório de casos reais (anonimizados ou pseudonimizados)

Mapeados em commits/Drive:
- **Feito-HBM** (Tema 1.258/STF) — catalogado em
  `engine/src/nexus/casos/data.py`; eixo dogmático claro
- **Feito-FB** (Felipe Barbalho — Maria da Penha, Tema 1.249/STJ) —
  documentado em `docs/casos/teses-feito-fb.md`
- **Outros vistos no Drive (não catalogados no engine):** Mario/Jefferson
  (RCL + HC + Apelação contra ato em SC), Raphael Kefale (Resp à Acusação +
  Memoriais Júri), Patrick Xavier (ED STJ), Geilson Satiro (Memorial
  Olinda), Vanessa e Bruna (RCL STF), Teixeira (HC STJ + ED TJPE),
  Edgleisson Carlos (HC STJ), Manoel Mota da Cruz, Denilson José (busca
  pessoal e domiciliar)

Cada um, no ciclo TIER 0, gera um **Romaneio de Revisão** (formato visto em
`ROMANEIO DE REVISAO — RAPHAEL`) com classificação **[NÍVEL 1 — DISPARAR]**
ou **[NÍVEL 2 — CONDICIONADA]** + condições explícitas a fechar.

## 6. Sinais externos de risco (a IA externa ignora; nós levamos a sério)

Casos reais públicos que confirmam por que o TIER 0 §0 (princípio raiz —
nada de fato/citação sem fonte primária lida) **não é academicismo**:

- **TJ-PR não analisa recurso em que IA criou precedentes e relatores**
  ([ConJur, 2025-abr-27](https://www.conjur.com.br/2025-abr-27/tj-pr-nao-analisa-recurso-gerado-por-ia-que-inventou-precedentes-e-relatores/))
  — alucinação jurisprudencial gera sanção processual.
- **Juiz multa advogadas que esconderam prompt em petição para enganar IA
  da Justiça** ([Migalhas, 455817](https://www.migalhas.com.br/quentes/455817/juiz-multa-advogadas-que-esconderam-prompt-para-enganar-ia-da-justica))
  — manipular tooling de IA gera multa.
- **Dicas para quem usa escondido IA generativa no processo penal**
  ([ConJur, 2026-jan-09](https://www.conjur.com.br/2026-jan-09/dicas-para-quem-usa-escondido-ia-generativa-no-processo-penal/))
  — uso sem transparência é problema.

**Como o ecossistema responde:**
- Princípio raiz TIER 0 + HALT do engine bloqueiam alucinação na origem.
- Disclaimer obrigatório (commit `8e3a8f9`) torna o uso de IA transparente.
- Romaneio de Revisão (a implementar) força o curador-humano a fechar
  condições antes do protocolo.

## 7. Decisões estratégicas em aberto

| Decisão | Estado | Próximo passo |
|---|---|---|
| Nome canônico produto | **Nexus** (escolhido) | aplicado em código, docs, brand |
| Stack | **Python/FastAPI** (escolhido) | mantido |
| Direção comercial | "marketplace agora" (escolhido), mas com gate OAB explícito no escopo §2 | parecer OAB/PE em paralelo ao código |
| Push do código | bloqueado por permissão da App | bundle entregue — aplicar localmente |
| TOS final | template em `docs/tos-template.md` | redação humana com advogado(a) |
| LGPD policy | rascunho técnico em `docs/lgpd.md` | revisão jurídica antes de publicar |
| Domínio frontend | `app.nexum.com.br` (sugerido) | registrar OU usar subdomínio em ribeiroetigre.org/.adv.br |

## 8. Próximos passos sugeridos (ordem de impacto)

1. **Destravar o push** (aplicar bundle local OU liberar GitHub App).
2. **Provisionar Railway** seguindo `docs/deploy.md` — engine no ar como
   infra interna do escritório, primeiro.
3. **Validar com Feito-HBM real** — primeiro ciclo end-to-end (signup →
   upload → /draft/llm → revisão humana → protocolo).
4. **Portar do audit:** `peca_tipo` enum expandido (HC, RHC, RCL,
   APELACAO, MEMORIAIS, RESPOSTA_ACUSACAO, EDCL, AGRG, MANIFESTACAO) +
   `modo_redacional` (PERTINAZ/ADAYLDO/PATRICK/MANUS).
5. **Implementar Romaneio de Revisão** (`GET /user/audits/{id}/romaneio`)
   no formato do Analista Primário.
6. **Construir `nexus/auditor.py`** implementando os 5 passos do
   ⇍AUDITOR FORENSE⇍ (anomalia temporal, cegueira deliberada, contágio).
7. **Extrair as 3 `.skill`** (especialmente `engenharia-juridica`) e
   incorporar `mapa_precedentes.md` ao catálogo do engine.
8. **Decidir posicionamento da landing:** `ribeiroetigre.org` continua
   como vitrine tecnológica que aponta para Inova by Tigre como produto
   público; Nexus permanece atrás como motor (commit `867cc42`).

## 9. Como ler este hub

Este é o documento-mestre. Quem entra novo no ecossistema (você, sua equipe,
um futuro Claude Code, um advogado-mentorado pelo Inova) começa **aqui**.
Daqui parte para:
- `tier-0-protocolo.md` — protocolo doutrinário canônico
- `recomendacao-estrategica.md` — julgamento sobre direção
- `marketplace-escopo.md` — escopo do MVP comercial
- `audit-drive-gems.md` — auditoria dos 8 gems + 3 skills
- `lgpd.md` / `tos-template.md` — camada legal
- `deploy.md` — operação Railway
- `engine/README.md` — uso do engine
