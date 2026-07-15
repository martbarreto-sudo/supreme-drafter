"""Ingestão dos autos digitais em PDF como blocos `document` da Messages API."""

from __future__ import annotations

import base64
from pathlib import Path

# Limites da API: 32 MB por requisição, 100 páginas em modelos de 200k / 600 em 1M.
MAX_PDF_BYTES = 32 * 1024 * 1024


def load_pdf_block(path: str | Path, *, citations: bool = True) -> dict:
    """Carrega um PDF local e devolve um bloco de conteúdo `document` (base64).

    Ativa citações para que o modelo possa ancorar cada facto na página de origem —
    reforçando o contrato de grounding (indicação de fls.).
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Autos não encontrados: {p}")

    raw = p.read_bytes()
    if not raw:
        raise ValueError(f"Arquivo vazio: {p}")
    if len(raw) > MAX_PDF_BYTES:
        raise ValueError(
            f"PDF excede 32 MB ({len(raw) / 1e6:.1f} MB). "
            "Divida os autos em volumes antes de auditar."
        )
    if raw[:5] != b"%PDF-":
        raise ValueError(f"Não parece um PDF válido (magic bytes): {p}")

    block: dict = {
        "type": "document",
        "source": {
            "type": "base64",
            "media_type": "application/pdf",
            "data": base64.standard_b64encode(raw).decode("ascii"),
        },
        "title": p.name,
    }
    if citations:
        block["citations"] = {"enabled": True}
    return block
