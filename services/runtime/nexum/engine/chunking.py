"""Chunking app-side de texto juridico para indexacao semantica.

Divide o texto em janelas de ~`target_tokens` com sobreposicao (`overlap_ratio`),
respeitando fronteiras de paragrafo/sentenca sempre que possivel e preservando a
ordem (`chunk_index` monotonico). Extrai a referencia de folha (`fls. N`) por
regex, conforme a doutrina Deep Hunter de rastreabilidade probatoria.

Deterministico e sem rede. O contador de tokens usa contagem por espacos em
branco como PROXY — um tokenizer real (ex.: tiktoken/sentencepiece) substituiria
`_count_tokens` sem alterar o restante do fluxo.
"""

from __future__ import annotations

import re
from typing import Callable, Optional

from pydantic import BaseModel, Field

# Extrator default de folha: primeira ocorrencia de "fls. 42", "fl 7", "fls42".
_FLS_RE = re.compile(r"fls?\.?\s*(\d+)", re.IGNORECASE)

# Fronteiras de paragrafo (linha em branco) e de sentenca. A sentenca so quebra
# quando a pontuacao e seguida por espaco E letra maiuscula, evitando partir
# abreviacoes juridicas comuns como "fls. 42" e "art. 386" (seguidas de digito).
_PARAGRAPH_RE = re.compile(r"\n\s*\n")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ])")


class Chunk(BaseModel):
    """Fragmento ordenado de uma source, pronto para embedding."""

    index: int = Field(ge=0)
    content: str
    fls_ref: Optional[str] = None
    token_count: int = Field(ge=0)


def _count_tokens(text: str) -> int:
    """Conta tokens por espacos em branco (PROXY de um tokenizer real)."""

    return len(text.split())


def default_fls_extractor(text: str) -> Optional[str]:
    """Extrai a primeira referencia `fls. N` de `text` (ou None)."""

    match = _FLS_RE.search(text)
    if match is None:
        return None
    return f"fls. {match.group(1)}"


def _split_units(text: str) -> list[str]:
    """Quebra o texto em unidades atomicas (sentencas dentro de paragrafos).

    Preserva a ordem do documento. Unidades vazias sao descartadas.
    """

    units: list[str] = []
    for paragraph in _PARAGRAPH_RE.split(text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        for sentence in _SENTENCE_RE.split(paragraph):
            sentence = sentence.strip()
            if sentence:
                units.append(sentence)
    return units


def chunk_text(
    text: str,
    *,
    target_tokens: int = 512,
    overlap_ratio: float = 0.12,
    fls_extractor: Optional[Callable[[str], Optional[str]]] = None,
) -> list[Chunk]:
    """Divide `text` em `Chunk`s de ~`target_tokens` tokens com sobreposicao.

    A sobreposicao (`overlap_ratio` * `target_tokens`, arredondada) repete os
    ultimos tokens do chunk anterior no inicio do proximo, preservando contexto
    entre fronteiras. As janelas respeitam fronteiras de sentenca/paragrafo (uma
    unidade nunca e partida ao meio). `fls_extractor` sobrescreve o extrator de
    folha default.

    Retorna lista possivelmente vazia (texto so com espacos => sem chunks), com
    `chunk_index` (campo `index`) comecando em 0 e estritamente crescente.
    """

    if target_tokens <= 0:
        raise ValueError("target_tokens deve ser positivo")
    if not 0.0 <= overlap_ratio < 1.0:
        raise ValueError("overlap_ratio deve estar em [0, 1)")

    extractor = fls_extractor or default_fls_extractor
    overlap_tokens = int(round(target_tokens * overlap_ratio))

    units = _split_units(text)
    if not units:
        return []

    chunks: list[Chunk] = []
    index = 0
    i = 0
    n = len(units)
    while i < n:
        window: list[str] = []
        tokens = 0
        j = i
        # Acumula unidades ate atingir ~target_tokens (sempre >= 1 unidade).
        while j < n:
            unit_tokens = _count_tokens(units[j])
            if window and tokens + unit_tokens > target_tokens:
                break
            window.append(units[j])
            tokens += unit_tokens
            j += 1

        content = " ".join(window)
        chunks.append(
            Chunk(
                index=index,
                content=content,
                fls_ref=extractor(content),
                token_count=_count_tokens(content),
            )
        )
        index += 1

        if j >= n:
            break

        # Recuo para sobreposicao: volta unidades ate cobrir ~overlap_tokens,
        # sem regredir alem do inicio da janela atual (garante progresso).
        back = 0
        acc = 0
        k = j - 1
        while k > i and acc < overlap_tokens:
            acc += _count_tokens(units[k])
            back += 1
            k -= 1
        i = j - back

    return chunks
