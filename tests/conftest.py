"""Stubs de teste: um cliente Anthropic falso que não faz rede, e um construtor
de PDFs estruturais (com *content stream* comprimido) partilhado pelos testes."""

from __future__ import annotations

import json
import zlib
from dataclasses import dataclass, field


# ── Construtor de PDFs de teste ──────────────────────────────────────────────


def build_pdf(
    content: bytes, *, compress: bool = True, filtro: bytes = b"/FlateDecode"
) -> bytes:
    """Monta um PDF mínimo, porém estrutural, com `content` como content stream."""
    corpo = zlib.compress(content) if compress else content
    dic = (
        b"<< /Length %d /Filter %s >>" % (len(corpo), filtro)
        if compress
        else b"<< /Length %d >>" % len(corpo)
    )
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        dic + b"\nstream\n" + corpo + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for numero, objeto in enumerate(objetos, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % numero + objeto + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1)
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objetos) + 1,
        xref,
    )
    return bytes(out)


def hex_utf16(texto: str) -> bytes:
    """String hexadecimal PDF em UTF-16BE, com BOM."""
    return b"<" + (b"\xfe\xff" + texto.encode("utf-16-be")).hex().upper().encode("ascii") + b">"


@dataclass
class FakeBlock:
    type: str
    text: str = ""


@dataclass
class FakeMessage:
    content: list
    stop_reason: str = "end_turn"
    stop_details: object | None = None


class _FakeStreamCtx:
    def __init__(self, message: FakeMessage):
        self._message = message

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self) -> FakeMessage:
        return self._message


@dataclass
class _Messages:
    parent: "FakeClient"

    def stream(self, **kwargs):
        self.parent.calls.append(kwargs)
        return _FakeStreamCtx(self.parent.next_message(kwargs))


@dataclass
class FakeClient:
    """Devolve dossiê ou peça consoante `output_config.format` esteja presente."""

    dossie: dict = field(default_factory=dict)
    peca: str = "# Peça de teste\n\n— Minuta"
    calls: list = field(default_factory=list)
    messages: _Messages = field(init=False)

    def __post_init__(self):
        self.messages = _Messages(self)

    def next_message(self, kwargs) -> FakeMessage:
        has_format = "format" in kwargs.get("output_config", {})
        if has_format:  # Deep Hunter → JSON
            return FakeMessage(
                content=[FakeBlock("text", json.dumps(self.dossie, ensure_ascii=False))]
            )
        return FakeMessage(content=[FakeBlock("text", self.peca)])  # Supreme Drafter
