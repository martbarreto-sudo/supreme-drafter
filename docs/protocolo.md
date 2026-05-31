# Protocolo Nexus by Tigre — Supreme Drafter

> Engine de redação estratégica criminal sob o dogma do **Dado Líquido**.
> Ribeiro & Tigre Advocacia Criminal · OAB/PE 27.543

---

## 1. HALT Ex-Officio

O **HALT Ex-Officio** é a regra-mãe do protocolo: a esteira de produção **interrompe automaticamente** a confecção de qualquer minuta quando detecta que um ou mais fatos da postulação carecem de auditoria contra fonte primária.

A premissa é que a assepsia processual exige simetria matemática absoluta entre a realidade dos autos e a postulação em juízo. Injetar dado de conveniência ou processo desalinhado na moldura recursal — especialmente em sede de cortes superiores — fornece ao Estado o pretexto perfeito para a inadmissibilidade imediata da insurgência por deficiência de fundamentação.

**Disparadores do HALT:**
- Fato proposto sem fonte primária correspondente (log do PJe, certidão, espelhamento forense)
- Indexação processual incorreta (peça migrada para sub-tema/tema alheio)
- Marco temporal fixado por aproximação e não por extração documental
- Citação doutrinária ou jurisprudencial sem `inteiro teor` localizado

**Saída do HALT:**
- Recusa fundamentada de minuta, com lista de vícios e ação de purgação
- A esteira só reabre após reinserção do **dado líquido** verificado

## 2. Módulo 11 — Algorithmic Bypass

Camada de validação que opera **antes** da geração de qualquer trecho dispositivo. Para cada fato declarado, o Módulo 11:

1. Exige um identificador de fonte primária (`log_pje://...`, `certidao://...`, `hash://...`)
2. Confronta o fato proposto contra o conteúdo da fonte
3. Marca cada item da minuta com um dos três status:
   - **LÍQUIDO** — verificado contra fonte primária
   - **PENDENTE** — aguardando inserção de fonte
   - **DESCARTADO** — diverge da fonte; não pode ser usado na peça

Nenhum fato em status PENDENTE ou DESCARTADO é incorporado à minuta final.

## 3. Dado Líquido

Princípio operacional: **só entra na peça o que pode ser provado documentalmente neste exato momento**. Conjectura, inferência razoável, e "deve ter sido" são vetados na fase dispositiva.

Conjectura útil entra apenas na fase argumentativa (teses), e sempre marcada como tal, jamais como afirmação de fato.

## 4. Temperatura Zero

Modo de execução em que a engine opera com determinismo máximo na fase dispositiva (relatório dos fatos, descrição do processo, citação de teses). Variação criativa fica restrita ao desenho retórico, e mesmo ali sob supervisão.

Em prática:
- LLM com `temperature=0` e `top_p=1`
- Templates jurídicos com substituição posicional, sem reescrita livre
- Validação pós-geração: tabela de vulnerabilidades (ver `tabela-vulnerabilidades.md`)

## 5. Auditoria de Silêncio

Antes do fechamento da minuta, a engine deve responder à pergunta:

> **O que o dossiê omitiu que impede a blindagem protetiva?**

Itens típicos auditados:
- Certidão de trânsito em julgado
- Cadeia incremental de hashes da fonte primária (dispositivo físico, log, áudio)
- Termo de desinteresse de órgãos auxiliares (NUDEM, DPPE, etc.)
- Espelhamento forense vs. cópia simples
- Limite temporal (decadência, prescrição, marco recursal)

Cada item omitido é reportado ao operador antes da assinatura.

## 6. Doutrina de Referência

Ver `doutrina.md`. As matrizes operacionais são: **Almeida Castro (KAKAY)**, **Toron**, **Tofic**.

## 7. Fluxo end-to-end

```
[Operador] → Dossiê + Relatório Ouro + Modo
        ↓
[Módulo 11] → Validação fato a fato (LÍQUIDO / PENDENTE / DESCARTADO)
        ↓
[HALT?] ── sim ──→ Recusa fundamentada
        │
        não
        ↓
[Templates · Temperatura Zero] → Minuta candidata
        ↓
[Auditoria de Silêncio] → Lista de omissões
        ↓
[Operador] → Assinatura ou retorno à fase de purgação
```

## 8. Glossário rápido

| Termo | Significado |
|---|---|
| **Tier 0** | Nível de acesso pleno à engine (operador titular) |
| **Dado Líquido** | Fato verificado contra fonte primária |
| **HALT** | Interrupção automática da esteira por vício de premissa |
| **Algorithmic Bypass** | Camada de validação que precede geração |
| **Temperatura Zero** | Modo determinístico de execução |
| **Dossiê** | Conjunto de fontes primárias entregue à engine |
| **Relatório Ouro** | Sumário curado dos fatos verificados |
| **Modo** | Tipo de peça (HC, RHC, Agravo, etc.) |
