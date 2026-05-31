# Nexum by Tigre — Estratégia de Produto, Precificação e Escala

> Documento vivo de análise. Tudo aqui é hipótese fundamentada — números de mercado precisam ser confirmados em pesquisa primária antes de virar política comercial. Pontos marcados com **⚠️** sinalizam premissas a validar.

---

## 1. Diagnóstico do estado atual

| Dimensão | Estado |
|---|---|
| Tecnologia | Landing estática + redirecionamento para Google NotebookLM. Engine real ainda não construído (Fases 3-4 do plano). |
| Operação | Tier 0 unipessoal — operador titular é o próprio Marcelo Tigre. |
| Doutrina | Mapeada (KAKAY, Toron, Tofic). Templates jurídicos ainda em forma tácita / NotebookLM. |
| Validação de fato | Protocolo HALT/Dado Líquido conceitualizado; ainda sem implementação algorítmica. |
| Mercado | Sem clientes externos. Sem precificação publicada. Sem contrato-modelo. |
| Marca | Forte conceitualmente ("Nexum by Tigre", Tier 0, estética dourado/dark). Ainda não opera como entidade comercial separada. |

**Implicação:** o produto hoje é **uma metodologia + uma marca**, sem o substrato técnico que justifique sua precificação como SaaS jurídico premium. A precificação abaixo é traçada para o **estado-alvo** (Fases 3-5 concluídas), com pontos de entrada intermediários.

## 2. Proposta de valor — onde está o "dinheiro líquido"

A diferenciação real do Nexum não é "IA jurídica" (commodity em 2025-2026), e sim a **conjunção de três eixos**:

1. **Anti-Alucinação como contrato de produto.** Protocolo HALT promete que nenhuma peça gerada conterá fato não-auditado. Em direito criminal, isto não é feature — é **redução de risco de inadmissibilidade**, que tem preço sombra altíssimo (perda do remédio heroico, prescrição, etc.).
2. **Doutrina DNA-criminal brasileira.** KAKAY, Toron, Tofic não são citação de marketing — são as matrizes que orientam a lógica de *distinguishing*, audição de silêncio e desenho retórico. Engines genéricos não têm isso embutido.
3. **Tier 0 como posicionamento.** Acesso curado, não self-serve indiscriminado. O cliente compra **escassez controlada** + reputação Ribeiro & Tigre.

Eixo extra (futuro): **integração PJe / indexadores** (Athos, Sócrates) para automação da auditoria de fatos. Esse é o multiplicador, mas exige fôlego técnico.

## 3. Quem paga — segmentação

| Segmento | Tamanho ⚠️ | Dor principal | Disposição a pagar |
|---|---|---|---|
| **A. Boutiques criminais top-tier (Br)** | ~50-200 escritórios | Volume de peças complexas, padrão de qualidade alto | **Alta** — R$ 5-30k/mês por escritório plausível |
| **B. Bancas individuais especializadas** | ~2.000-5.000 advogados | Solidão técnica em peças de cortes superiores | **Média-alta** — R$ 800-3.000/mês por seat |
| **C. Defensorias / convênios** | ~30 estaduais + federal | Volume massivo, recursos limitados | **Baixa-média** — contratos públicos, licitação |
| **D. Departamentos jurídicos corporativos** | nicho | Acompanhar casos criminais de executivos | **Alta**, mas raro |
| **E. Cursinhos / prep OAB / ensino** | ~50 grandes players | Conteúdo doutrinário sistematizado | **Baixa** — licenciamento de conteúdo, não engine |

**Hipótese de foco inicial:** **A + B**. Defensorias e ensino são distrações nesta fase — exigem produtos diferentes.

## 4. Modelos de precificação considerados

### 4.1. SaaS por seat (recorrente)
- **Estrutura:** R$ X / mês / advogado.
- **Faixa ⚠️:** R$ 1.500 a 4.000 / mês / seat para Segmento B; R$ 3.000-8.000 para Segmento A.
- **Prós:** Previsível, escalável, fácil de comunicar.
- **Contras:** Não captura assimetria de uso (um escritório que gera 50 peças/mês paga o mesmo que um que gera 2).

### 4.2. Crédito por peça (consumo)
- **Estrutura:** Assinatura base + pacotes de "peças líquidas". HC simples = N créditos, RHC = M, *distinguishing* em corte superior = K.
- **Faixa ⚠️:** R$ 600-2.500 por peça gerada (uma peça crítica de corte superior facilmente vale 10-50x esse valor em honorários do escritório).
- **Prós:** Alinha receita com valor entregue; captura usuário de alto volume.
- **Contras:** Operacionalmente pesado (medir uso, faturar variável); cria atrito em decisão de uso.

### 4.3. Licenciamento Tier (acesso curado)
- **Estrutura:** Camadas anuais, número fixo de seats por tier.
  - **Tier 0 — Fundador / Operador Titular:** R$ 0 (uso interno Ribeiro & Tigre)
  - **Tier 1 — Inner Circle:** 5-10 escritórios convidados, **R$ 80-150k/ano** ⚠️ por escritório, sem limite de peças, onboarding pessoal de Marcelo.
  - **Tier 2 — Acesso Profissional:** SaaS self-serve, **R$ 2.500-4.000/mês/seat** ⚠️, capacidade técnica + suporte assíncrono.
  - **Tier 3 — Inteligência (futuro):** API/white-label para legal-techs, contrato custom.
- **Prós:** Alinha com a marca Tier 0; cria escassez; permite cobrar premium do Inner Circle.
- **Contras:** Vendas longas no Tier 1; risco de pequeno mercado se o premium não for absorvido.

### 4.4. Outcome-based — **rejeitada**
Pagar conforme êxito do remédio criminal soa apelativo, mas:
- **Eticamente cinzento** sob o CED-OAB e Provimento CFOAB sobre publicidade/honorários.
- Cria conflito entre o que a engine recomenda e o que o operador deve decidir.
- Mistura responsabilidade técnica (advogado) com risco de produto (engine).

> **Recomendação:** descartar outcome-based como modelo público; pode existir como **pacto privado** entre Marcelo e cliente fora do contrato da engine.

### 4.5. Híbrido recomendado (proposta)
**Tier 1 (Inner Circle)** anual + **Tier 2 (Profissional)** mensal por seat + **add-on de peças complexas** para clientes Tier 2 de alto volume. Isto:
- Captura o premium (Tier 1)
- Permite escala (Tier 2)
- Não deixa dinheiro na mesa em casos pesados (add-on)

## 5. Estimativa de receita-piloto ⚠️

**Cenário conservador, 12 meses pós-Fase 4:**

| Item | Volume | Ticket | Receita anual |
|---|---|---|---|
| Tier 1 — Inner Circle | 5 escritórios | R$ 100k/ano | R$ 500k |
| Tier 2 — Profissional | 30 seats | R$ 3k/mês | R$ 1,08M |
| Add-on peças (Tier 2) | 200 peças/ano | R$ 1,5k | R$ 300k |
| **Total ARR ano 1** | | | **~R$ 1,9M** |

**Custos diretos relevantes (estimativa):**
- LLM (Claude Sonnet 4.6 + prompt caching) para ~5.000 peças/ano: **R$ 80-180k/ano** ⚠️
- Infra (host, observabilidade, backups LGPD): **R$ 60-120k/ano**
- Conteúdo doutrinário/curadoria (parte do tempo de Marcelo + 1 paralegal): **R$ 200-400k/ano**

**Margem bruta-alvo:** > 70% (típico SaaS técnico) — atingível se o uso de LLM for bem gerido (caching, modelos menores em sub-tarefas).

## 6. Metodologia de escala

Estágios sequenciais, **não paralelos**. Cada estágio precisa ser provado antes do próximo.

### Estágio 0 — Validação interna (3-6 meses)
- Engine MVP roda na própria rotina do escritório Ribeiro & Tigre.
- Métrica: **redução de tempo médio por peça** (HC, RHC) e **zero erros de Dado Líquido** detectados pós-protocolo.
- Sem cobrança externa. Saída: case study interno auditável.

### Estágio 1 — Inner Circle (6-12 meses)
- Convidar **3-5 escritórios** de confiança pessoal de Marcelo.
- Onboarding presencial. Contrato anual. NDA bilateral.
- Métrica: **NPS ≥ 70**, retenção 100%, **3 case studies externos** documentados.
- Risco principal: dependência do tempo pessoal de Marcelo. Mitigação: cap em N escritórios.

### Estágio 2 — Profissional (12-18 meses)
- Self-serve SaaS para Segmento B.
- Onboarding remoto + biblioteca de templates.
- Métrica: **CAC < 1/3 LTV**, churn mensal < 3%.
- Risco principal: suporte vira gargalo. Mitigação: comunidade Slack/Discord curada + base de conhecimento.

### Estágio 3 — Plataforma (18-36 meses)
- API + white-label para legal-techs e editoras jurídicas.
- Métrica: 2-3 parcerias âncora.
- Risco principal: diluição da marca. Mitigação: white-label sem co-branding em peças finais.

### Princípios não-negociáveis durante a escala

1. **Tier 0 não escala.** Marcelo continua sendo o operador titular do próprio escritório, não vira "founder a tempo parcial" do produto. Se o produto exigir mais do que ele pode dar, contrata-se equipe técnica — não se dilui o operador.
2. **Cliente externo nunca opera Tier 0.** Tier 0 é selo, não cargo vendável.
3. **HALT é cláusula de produto.** Se o protocolo HALT falhar em entregar zero alucinações em fatos dispositivos, a engine **suspende emissão**, não emite peça degradada. Isto vai no contrato de serviço.
4. **LGPD por construção.** Dados de processo nunca entram no repo nem em prompt de LLM sem anonimização ou contrato de operador.

## 7. Restrições regulatórias (não ignorar)

- **CED-OAB e publicidade:** marketing do Nexum não pode prometer resultado, sustentar superioridade comparativa entre advogados, ou usar nomes de clientes sem autorização.
- **Sigilo profissional:** dados de cliente do escritório de Marcelo não podem servir de training data sem consentimento — mesmo anonimizados.
- **LGPD + segredo de justiça:** logs de PJe, dados pessoais sensíveis (saúde, orientação, etc.) exigem tratamento específico, contrato de operação, e provavelmente DPO.
- **Responsabilidade técnica:** a engine é ferramenta — o advogado-operador é o responsável final pela peça. Isto precisa estar **explícito no contrato** com cliente Tier 1/2 para evitar transferência indevida de responsabilidade.

## 8. Roadmap de evolução do engine (priorizado)

Ordem por **maior alavanca / menor risco**:

1. **Fase 3 (já planejada):** MVP determinístico — HALT, Dado Líquido, templates Jinja2, sem LLM. Garante que o protocolo opera sozinho.
2. **Fase 4 (já planejada):** Caso-piloto Feito-HBM com Claude Sonnet 4.6 + prompt caching. Valida que LLM respeita HALT.
3. **Knowledge Base doutrinária (RAG):** KAKAY, Toron, Tofic + temas STF/STJ relevantes em base vetorial. Precisa de licenciamento ou citação justa.
4. **Ingestão PJe:** scraping ou API quando disponível. Maior alavanca operacional, mas burocrática (cada tribunal tem regra).
5. **Auditoria automatizada Athos/Sócrates:** validação cruzada de indexação processual antes da minuta. Reduz risco de erro tipo "Feito-2 / Súmula 231".
6. **Multi-tenant + RBAC:** quando entrar em Tier 1/2 com múltiplos escritórios.
7. **Observabilidade jurídica:** dashboard de Vulnerabilidades por feito, tempo médio até peça líquida, taxa de HALT por operador. Vira também relatório executivo para o Inner Circle.

## 9. Riscos a monitorar

| Risco | Impacto | Mitigação |
|---|---|---|
| Concorrente lança "anti-hallucination first" antes | Alto | Velocidade no Fase 3-4; publicar metodologia (não o engine); marca registrada de "Dado Líquido" / "HALT Ex-Officio" |
| LLM vendor lock-in / mudança de preço Anthropic | Médio | Abstração da camada LLM; testes com modelos alternativos |
| Tempo pessoal de Marcelo vira gargalo | Alto | Cap rígido no Inner Circle; equipe técnica externa |
| Cliente Tier 1 usa engine de forma negligente e gera passivo | Alto | Cláusula contratual de responsabilidade técnica do advogado-operador; logs de auditoria para defesa |
| LGPD/OAB intervenção | Alto | DPO + parecer jurídico próprio sobre o contrato-modelo antes de Tier 1 |

## 10. Próximas decisões que o operador titular precisa tomar

1. **Confirma o foco em Segmentos A + B?** Se não, qual?
2. **Aceita o modelo híbrido (Tier 1 anual + Tier 2 mensal + add-on)?**
3. **Qual o teto de Inner Circle?** (Sugestão: 5)
4. **Quando começar Estágio 1?** (Sugestão: depois da Fase 4 do engine — caso-piloto Feito-HBM validado)
5. **Marca registrada de "Dado Líquido" e "HALT Ex-Officio" — registrar agora ou esperar?** (Recomendação: registrar agora — INPI é lento)

## 11. Modelo de receita escalonado em 3 camadas (proposta a auditar)

Proposta de monetização em três camadas, capturando receita proporcional ao impacto.
Convergente com o modelo híbrido do §4.5, mas com unidades de cobrança distintas.
**Números são hipótese ⚠️ — precisam de pesquisa primária; e há um risco OAB sério
na camada 2 que precisa de parecer antes de qualquer execução.**

| Camada | Unidade | Faixa ⚠️ | Margem-alvo ⚠️ | Quem paga |
|---|---|---|---|---|
| **1. Análise de Risco (SaaS por caso)** | por análise | R$ 500–2.000 | 60–75% | Advogados independentes / pequenos escritórios |
| **2. Parecer Estruturado (marketplace)** | comissão sobre parecer premium (`quality_score` > 85) | 30–40% de R$ 5–15k | ~85% | Escritórios médios |
| **3. Acesso Corporativo (retainer)** | mensal, acesso ilimitado | R$ 50–200k/mês | ~90% | Tribunais, Defensoria, grandes escritórios |

**Como resolve a tensão quantidade × qualidade:** segmenta o mercado pela unidade de
cobrança — volume (camada 1), qualidade (camada 2), confiança (camada 3).

### ⚠️ Bandeiras vermelhas a resolver ANTES de executar

1. **Camada 2 (marketplace de pareceres) é o maior risco OAB.** Comercializar "parecer
   jurídico premium" com comissão a terceiros esbarra em: vedação à mercantilização da
   advocacia, captação de clientela, e responsabilidade técnica de quem assina o parecer.
   `quality_score > 85` **não** torna um documento um parecer assinável — gate heurístico
   não é responsabilidade profissional. **Esta camada precisa de parecer formal da OAB/PE
   antes de qualquer linha de código.** Pode ser inviável na forma proposta.
2. **Defensoria/Tribunais (camada 3) compram por licitação**, não por retainer comercial
   direto. O ciclo e as regras são outros — tratado no §3 como segmento de baixa prioridade.
3. **Números `+900 → +9.000 casos` e margens 60–90% não são auditados.** São aspiracionais.
   A margem real depende do custo de LLM por peça (ver §5) e do tempo humano de revisão —
   que **não desaparece**, porque o advogado-operador segue responsável.
4. **Infra de cobrança não existe** (Stripe, marketplace, painel corporativo, Google
   Workspace). É roadmap, não estado atual — ver `insights.md §1`.

### Recomendação

Executar **apenas a camada 1** (SaaS por análise) no piloto — é a de menor risco
regulatório e mapeia direto ao engine atual (`/draft/llm` + `quality_score`). Congelar
camada 2 até parecer OAB. Tratar camada 3 como venda consultiva caso-a-caso, não produto.
