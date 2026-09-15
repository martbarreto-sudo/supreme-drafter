"""Ingestão dos autos digitais em PDF como blocos `document` da Messages API."""

from __future__ import annotations

import base64
from pathlib import Path

# Limites da API: 32 MB por requisição, 100 páginas em modelos de 200k / 600 em 1M.
MAX_REQUEST_BYTES = 32 * 1024 * 1024
# O limite da API aplica-se ao corpo enviado, e base64 infla o ficheiro em ~4/3:
# aferir o PDF cru contra 32 MB deixava passar autos que a API recusaria depois de
# já terem sido lidos, codificados e transmitidos.
MAX_PDF_BYTES = MAX_REQUEST_BYTES * 3 // 4


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
            f"PDF de {len(raw) / 1e6:.1f} MB excede o teto de "
            f"{MAX_PDF_BYTES / 1e6:.1f} MB (32 MB de requisição menos a inflação "
            "de ~33% do base64). Divida os autos em volumes antes de auditar."
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
