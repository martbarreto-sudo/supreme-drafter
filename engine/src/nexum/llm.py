from __future__ import annotations

import os
from dataclasses import dataclass

import anthropic

from .models import Fato, Feito, PecaTipo

MODEL_DEFAULT = "claude-opus-4-8"

# System prompt — doutrina + protocolo. Mantido estável byte-a-byte para cache hit
# em todas as chamadas. Volatilidade (Feito, fatos) vai no user message.
SYSTEM_PROMPT = """Você é o Supreme Drafter — engine de redação jurídica criminal da Ribeiro & Tigre Advocacia Criminal (OAB/PE 27.543).

## Protocolo Nexum by Tigre

### HALT Ex-Officio
A esteira de produção interrompe-se ex-officio se qualquer fato dispositivo não estiver em status LIQUIDO. Você só recebe fatos já auditados pelo Módulo 11. Não invente fatos. Não infira. Não conjecture na seção dispositiva.

### Dado Líquido
Apenas fatos verificados contra fonte primária (log_pje://, certidao://, hash://, audio://, video://, peticao://) entram na peça dispositiva. Conjectura é vetada na fase dispositiva e só admitida na fase argumentativa, sempre marcada como tese.

### Temperatura Zero
Determinismo máximo no relatório dos fatos. O dispositivo cola na fonte primária — palavra por palavra quando possível. Variação criativa fica restrita ao desenho retórico da fase argumentativa.

### Auditoria de Silêncio
Antes do fechamento, responda: "O que o dossiê omitiu que impede a blindagem protetiva?". Liste os itens omitidos ao final da peça, em bloco separado.

## Doutrina de referência

### Antônio Carlos de Almeida Castro (KAKAY)
Combatividade radical em cortes superiores; arguição de nulidades de ordem pública; estancamento de abusos institucionais.

### Alberto Zacharias Toron
Micro-desconstrução cirúrgica; fragmentação ponto a ponto de laudos, denúncias e decretos genéricos; rigor processual intolerante a bases empíricas instáveis.

### Tofic
Distinguishing fático rigoroso; superação sumular por isolamento de teses de alta densidade; admissibilidade recursal blindada.

## Assinatura Tigre

Orações curtas, modo imperativo, eliminação de adjetivação inútil, eliminação do `data venia` submisso, foco em escaneabilidade (Legal Design).

## Formato de saída

Estruture a minuta com estes blocos, nesta ordem:

1. **CABEÇALHO** — tipo da peça + ID do feito + quadrante dogmático + eixo
2. **I. DOS FATOS** — relato dos fatos líquidos, citando a fonte primária em cada item
3. **II. TABELA DE VULNERABILIDADES** — em markdown, com as vulnerabilidades fornecidas verbatim
4. **III. DO DIREITO** — distinguishing/teses ancoradas no eixo dogmático; cite o precedente-chave explicitamente
5. **IV. DOS PEDIDOS** — pedido cautelar (se aplicável ao modo) e pedido de mérito
6. **AUDITORIA DE SILÊNCIO** — lista do que o dossiê não entregou e que poderia ser determinante

Nunca inclua fatos não-fornecidos. Nunca omita o precedente-chave do eixo dogmático. Nunca acrescente data venia, "ousamos", ou submissão burocrática.
"""


@dataclass
class MinutaLLM:
    texto: str
    modelo: str
    input_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    output_tokens: int


def gerar_minuta(
    feito: Feito,
    fatos: list[Fato],
    peca_tipo: PecaTipo,
    modo: str = "PERTINAZ",
    client: anthropic.Anthropic | None = None,
) -> MinutaLLM:
    if client is None:
        client = anthropic.Anthropic()

    modelo = os.getenv("NEXUM_MODEL", MODEL_DEFAULT)
    user_message = _montar_user_message(feito, fatos, peca_tipo, modo)

    response = client.messages.create(
        model=modelo,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    texto = "\n".join(b.text for b in response.content if b.type == "text")
    usage = response.usage

    return MinutaLLM(
        texto=texto,
        modelo=modelo,
        input_tokens=usage.input_tokens,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
        cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        output_tokens=usage.output_tokens,
    )


def _montar_user_message(
    feito: Feito, fatos: list[Fato], peca_tipo: PecaTipo, modo: str
) -> str:
    fatos_md = "\n".join(
        f"- **{f.id}**: {f.verificado} (fonte: `{f.fonte.uri}`)"
        for f in fatos
        if f.dispositivo and f.fonte is not None
    )

    vulns_md = "\n".join(
        f"| {v.fato_id} | {v.proposto} | {v.realidade_verificada} | {v.status.value} | {v.impacto} |"
        for v in feito.vulnerabilidades
    )

    return f"""Gerar **{peca_tipo}** em modo **[{modo}]** para o feito **{feito.id}**.

## Feito
- ID: {feito.id}
- Quadrante: {feito.quadrante}
- Eixo dogmático: {feito.eixo_dogmatico}

## Fatos líquidos (já auditados pelo Módulo 11)
{fatos_md}

## Tabela de vulnerabilidades (incluir verbatim na peça, no bloco II)
| fato_id | Proposto | Realidade Verificada | Status | Impacto |
|---|---|---|---|---|
{vulns_md}

Gere a minuta seguindo o formato definido no system prompt. Sob Temperatura Zero, mantenha o relato dos fatos estritamente colado nas fontes primárias acima."""


# --- Validação pós-geração para o caso-piloto Feito-HBM ---

def validar_feito_hbm(minuta: str) -> list[str]:
    """Retorna a lista de asserções não satisfeitas para o caso-piloto Feito-HBM.

    Lista vazia = peça aprovada nas três asserções da Fase 4 do plano.
    """
    falhas: list[str] = []
    if "Tema 1.258" not in minuta and "Tema 1258" not in minuta:
        falhas.append("Distinguishing contra Tema 1.258/STF ausente")
    if "598.887" not in minuta and "598887" not in minuta:
        falhas.append("Citação ao HC 598.887/SC ausente")
    upper = minuta.upper()
    if "VULNERABILIDADES" not in upper:
        falhas.append("Tabela de vulnerabilidades ausente")
    return falhas
