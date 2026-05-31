"""Upload de autos — gera hash SHA-256 que ancora a fonte primária `hash://`.

Persiste o binário em $CASO_DATA_DIR (volume controlado pelo operador, fora do repo).
O retorno traz o `fonte_uri` que pode ser usado como `fonte.uri` em /draft/llm —
plugando o upload diretamente no Dado Líquido. Sem OCR/extração nesta fase.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from fastapi import HTTPException, UploadFile

MAX_BYTES = 20 * 1024 * 1024  # 20 MiB
ALLOWED_MIME = {"application/pdf"}
_FEITO_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def _caso_data_dir() -> Path:
    raw = os.getenv("CASO_DATA_DIR")
    if not raw:
        raise HTTPException(503, "CASO_DATA_DIR não configurado — uploads desabilitados")
    p = Path(raw)
    if not p.is_dir():
        raise HTTPException(503, f"CASO_DATA_DIR não é diretório: {raw}")
    return p


async def receber_autos(
    user_id: str, feito_id: str, arquivo: UploadFile
) -> dict[str, str]:
    if not _FEITO_RE.match(feito_id):
        raise HTTPException(400, "feito_id inválido (use [A-Za-z0-9_-])")
    if arquivo.content_type not in ALLOWED_MIME:
        raise HTTPException(415, f"Tipo não suportado: {arquivo.content_type}; só PDF")

    h = hashlib.sha256()
    total = 0
    chunks: list[bytes] = []
    while chunk := await arquivo.read(64 * 1024):
        total += len(chunk)
        if total > MAX_BYTES:
            raise HTTPException(413, f"Arquivo excede {MAX_BYTES} bytes")
        h.update(chunk)
        chunks.append(chunk)

    sha256 = h.hexdigest()
    # Isolamento por user_id — uploads de cada advogado ficam em diretório próprio
    base = _caso_data_dir() / user_id / feito_id
    base.mkdir(parents=True, exist_ok=True)
    dest = base / f"{sha256}.pdf"
    if not dest.exists():
        with dest.open("wb") as f:
            for c in chunks:
                f.write(c)

    return {
        "feito_id": feito_id,
        "sha256": sha256,
        "fonte_uri": f"hash://{feito_id}/{sha256}",
        "bytes": str(total),
    }
