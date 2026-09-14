"""Extração de texto dos autos em PDF — stdlib pura, sem rede e sem dependências.

Motivação (regressão corrigida): a varredura de termos do auditor local lia os bytes
crus do PDF em `latin-1`. Num PDF real o texto vive dentro de *content streams*
comprimidos (`/Filter /FlateDecode`), logo a varredura não encontrava nada e **todo
processo real era classificado como "seco"** — omissões sinalizadas e cadeia de
custódia dada por quebrada mesmo quando os autos traziam hash, ata e portaria. Num
instrumento forense esse é o pior modo de falha possível: fabricar nulidades
inexistentes. Este módulo fecha esse buraco.

Estratégia (por ordem, primeira que render texto vence):

1. **Extractor stdlib** (padrão): localiza os *content streams*, infla o que for
   deflate (`zlib`) e interpreta os operadores de exibição de texto
   (``Tj``, ``TJ``, ``'``, ``"``), remontando palavras partidas por kerning dentro
   dos vectores ``TJ``.
2. **pypdf**, se estiver instalado — maior fidelidade em fontes com codificação
   própria. É *opcional* e só entra quando (1) nada devolve, de modo que a
   instalação padrão permaneça determinística e reprodutível.
3. **Varredura crua** em `latin-1` — resgate para PDFs sem streams (fixtures de
   teste, PDFs lineares não comprimidos).

Limites conhecidos (é best-effort, não é um parser PDF completo): não resolve
`/Length` indirecto (delimita pelo primeiro ``endstream``), não decifra PDFs
encriptados e não aplica `/Differences` de codificação de fonte. Para perícia real,
`pypdf`/`pdfplumber` continuam a ser o caminho.
"""

from __future__ import annotations

import re
import unicodedata
import zlib

# Classes léxicas do PDF (ISO 32000-1, §7.2).
_WS = b"\x00\t\n\f\r "
_DELIMS = b"()<>[]{}/%"
# Operadores que efectivamente pintam texto na página.
_TEXT_OPS = {b"Tj", b"TJ", b"'", b'"'}

_ESCAPES = {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b", b"f": b"\f"}
# Número PDF (§7.3.3): inteiro ou real, com sinal opcional. Um número NÃO é operador,
# logo não encerra o lote de strings — é o que mantém inteiro o kerning fraccionário
# de `[(cont) -12.5 (emporaneidade)] TJ`.
_NUMERO = re.compile(rb"^[+-]?(?:\d+\.?\d*|\.\d+)$")
# Marcas de um content stream com texto; filtram streams de imagem e de dados.
_MARCAS_TEXTO = (b"BT", b"Tj", b"TJ")


# ── Leitura de strings PDF ───────────────────────────────────────────────────


def _read_literal(data: bytes, i: int) -> tuple[bytes, int]:
    """Lê uma string literal `( ... )` a partir de `data[i] == b"("`.

    Trata parênteses aninhados, escapes simbólicos, octais (`\\ddd`) e a
    continuação de linha (`\\` seguido de fim de linha).
    """
    i += 1
    depth = 1
    buf = bytearray()
    n = len(data)
    while i < n:
        ch = data[i : i + 1]
        if ch == b"\\":
            i += 1
            esc = data[i : i + 1]
            if not esc:
                break
            if esc in _ESCAPES:
                buf += _ESCAPES[esc]
                i += 1
            elif esc.isdigit() and esc in b"01234567":
                octal = bytearray()
                while i < n and len(octal) < 3 and data[i : i + 1] in b"01234567":
                    octal += data[i : i + 1]
                    i += 1
                buf.append(int(octal, 8) & 0xFF)
            elif esc == b"\n":
                i += 1
            elif esc == b"\r":
                i += 1
                if data[i : i + 1] == b"\n":
                    i += 1
            else:  # `\(`, `\)`, `\\` e quaisquer outros: o próprio carácter.
                buf += esc
                i += 1
            continue
        if ch == b"(":
            depth += 1
            buf += ch
        elif ch == b")":
            depth -= 1
            i += 1
            if depth == 0:
                return bytes(buf), i
            buf += ch
            continue
        else:
            buf += ch
        i += 1
    return bytes(buf), i


def _read_hex(data: bytes, i: int) -> tuple[bytes, int]:
    """Lê uma string hexadecimal `<48656C6C6F>` a partir de `data[i] == b"<"`."""
    end = data.find(b">", i + 1)
    if end < 0:
        return b"", len(data)
    digits = bytes(c for c in data[i + 1 : end] if c in b"0123456789abcdefABCDEF")
    if len(digits) % 2:  # dígito ímpar final → completa com zero (§7.3.4.3).
        digits += b"0"
    try:
        return bytes.fromhex(digits.decode("ascii")), end + 1
    except ValueError:
        return b"", end + 1


def _decode(raw: bytes) -> str:
    """Converte uma string PDF em texto (UTF-16BE quando marcada por BOM)."""
    if raw[:2] == b"\xfe\xff":
        return raw[2:].decode("utf-16-be", errors="ignore")
    return raw.decode("latin-1", errors="ignore")


# ── Interpretação do content stream ──────────────────────────────────────────


def _text_from_content(data: bytes) -> str:
    """Devolve o texto exibido por um *content stream*.

    Acumula as strings encontradas e só as emite quando surge um operador de
    exibição — assim nomes, dicionários e argumentos que nunca chegam à página
    ficam de fora. As strings de um mesmo vector ``TJ`` são concatenadas sem
    separador, o que remonta palavras partidas por ajuste de kerning
    (``[(cont) -20 (emporaneidade)] TJ`` → ``contemporaneidade``).
    """
    linhas: list[str] = []
    pendentes: list[bytes] = []
    i, n = 0, len(data)

    while i < n:
        ch = data[i : i + 1]

        if ch == b"(":
            texto, i = _read_literal(data, i)
            pendentes.append(texto)
        elif ch == b"<":
            if data[i + 1 : i + 2] == b"<":  # abertura de dicionário
                i += 2
            else:
                texto, i = _read_hex(data, i)
                pendentes.append(texto)
        elif ch == b">":
            i += 2 if data[i + 1 : i + 2] == b">" else 1
        elif ch == b"%":  # comentário até ao fim da linha
            quebra = data.find(b"\n", i)
            i = n if quebra < 0 else quebra + 1
        elif ch == b"/":  # nome (/F1, /Type…): consome e descarta
            i += 1
            while i < n and data[i] not in _WS and data[i] not in _DELIMS:
                i += 1
        elif ch in b"[]{}":
            i += 1
        elif data[i] in _WS:
            i += 1
        else:  # token regular: número ou operador
            inicio = i
            while i < n and data[i] not in _WS and data[i] not in _DELIMS:
                i += 1
            if i == inicio:  # salvaguarda contra ciclo infinito
                i += 1
                continue
            token = data[inicio:i]
            if token in _TEXT_OPS:
                if pendentes:
                    linhas.append(_decode(b"".join(pendentes)))
            # Qualquer operador encerra o lote: strings não exibidas são descartadas.
            if not _NUMERO.match(token):
                pendentes.clear()

    return "\n".join(linhas)


# ── Localização e descompressão dos streams ──────────────────────────────────


def _inflar(corpo: bytes) -> bytes:
    """Infla um stream deflate; devolve-o intacto se não for comprimido.

    Aceita dados truncados (`decompressobj`) e deflate cru (`wbits=-15`), ambos
    frequentes em PDFs gerados por ferramentas menos rigorosas.
    """
    for tentativa in (
        lambda: zlib.decompress(corpo),
        lambda: zlib.decompressobj().decompress(corpo),
        lambda: zlib.decompressobj(-15).decompress(corpo),
    ):
        try:
            inflado = tentativa()
        except zlib.error:
            continue
        if inflado:
            return inflado
    return corpo  # não comprimido (ou filtro que não sabemos desfazer)


def _iter_streams(raw: bytes):
    """Percorre os pares `stream`/`endstream` do ficheiro."""
    pos = 0
    n = len(raw)
    while pos < n:
        k = raw.find(b"stream", pos)
        if k < 0:
            return
        if k >= 3 and raw[k - 3 : k] == b"end":  # apanhou o `endstream` de outro objecto
            pos = k + 6
            continue
        inicio = k + 6
        if raw[inicio : inicio + 2] == b"\r\n":
            inicio += 2
        elif raw[inicio : inicio + 1] in (b"\n", b"\r"):
            inicio += 1
        fim = raw.find(b"endstream", inicio)
        if fim < 0:
            yield raw[inicio:]
            return
        yield raw[inicio:fim].rstrip(b"\r\n")
        pos = fim + 9


def _parece_content_stream(dados: bytes) -> bool:
    """Um stream só é interpretado se trouxer marcas de texto.

    Sem esta guarda, um stream de imagem (`/DCTDecode`) que a descompressão não
    desfaz seria varrido como se fosse texto, e qualquer sequência entre parênteses
    no binário viraria "facto" dos autos.
    """
    return any(marca in dados for marca in _MARCAS_TEXTO)


def _extrair_stdlib(raw: bytes) -> str:
    partes = []
    for corpo in _iter_streams(raw):
        dados = _inflar(corpo)
        if not _parece_content_stream(dados):
            continue
        texto = _text_from_content(dados)
        if texto.strip():
            partes.append(texto)
    return "\n".join(partes)


def _tem_streams(raw: bytes) -> bool:
    return next(_iter_streams(raw), None) is not None


def _extrair_pypdf(raw: bytes) -> str:
    """Tentativa opcional via pypdf (maior fidelidade); silenciosa se ausente."""
    try:
        import io

        from pypdf import PdfReader
    except ImportError:
        return ""
    try:
        leitor = PdfReader(io.BytesIO(raw))
        return "\n".join((pagina.extract_text() or "") for pagina in leitor.pages)
    except Exception:  # pypdf levanta uma família larga de erros em PDFs sujos
        return ""


def _extrair_cru(raw: bytes) -> str:
    """Resgate: texto solto no corpo do ficheiro (PDFs sem streams comprimidos)."""
    return raw.decode("latin-1", errors="ignore")


def extract_text(raw: bytes) -> str:
    """Devolve o melhor texto disponível para os bytes de um PDF.

    Nunca levanta excepção por conteúdo malformado. A validação do PDF em si é
    responsabilidade do chamador.

    O resgate cru aplica-se **apenas** a ficheiros sem streams. Num PDF que tem
    streams mas de onde nada se extraiu, varrer os bytes crus devolveria o binário
    das imagens e dos objectos — e um termo encontrado nesse lixo seria tomado por
    facto dos autos. Nesse caso a resposta honesta é cadeia vazia.
    """
    for extractor in (_extrair_stdlib, _extrair_pypdf):
        texto = extractor(raw)
        if texto.strip():
            return texto
    return _extrair_cru(raw) if not _tem_streams(raw) else ""


def normalizar(texto: str) -> str:
    """Minúsculas sem acentos e com espaçamento colapsado, para varredura de termos.

    Torna a detecção insensível à acentuação (`plenário` ≡ `plenario`) e imune a
    quebras de linha inseridas pela paginação.
    """
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    sem_acentos = "".join(c for c in decomposto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acentos)
