"""Persiste auditorias — escreve minuta no disco e registra metadados em DB.

Layout no disco: $CASO_DATA_DIR/{user_id}/audits/{audit_id}.md
Por que arquivo e não TEXT no DB: minutas podem ter dezenas de KB; manter
fora do DB reduz custo de query/backup e permite streaming direto.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from nexus.db.models import Audit


class CasoDataDirAusente(Exception):
    pass


class MinutaNaoEncontrada(Exception):
    pass


class RomaneioNaoEncontrado(Exception):
    pass


def _base_dir() -> Path:
    raw = os.getenv("CASO_DATA_DIR")
    if not raw:
        raise CasoDataDirAusente("CASO_DATA_DIR não configurado")
    return Path(raw)


async def gravar_audit(
    session: AsyncSession,
    *,
    user_id: str,
    feito_id: str,
    peca_tipo: str,
    minuta_texto: str,
    quality_score: int,
    modelo: str,
    input_tokens: int = 0,
    cache_read_tokens: int = 0,
    cache_creation_tokens: int = 0,
    output_tokens: int = 0,
) -> Audit:
    audit = Audit(
        user_id=user_id,
        feito_id=feito_id,
        peca_tipo=peca_tipo,
        quality_score=quality_score,
        modelo=modelo,
        minuta_path="",  # preenchido após gerar audit.id
        input_tokens=input_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_creation_tokens=cache_creation_tokens,
        output_tokens=output_tokens,
    )
    session.add(audit)
    await session.flush()  # popula audit.id antes de montar caminho

    audit_dir = _base_dir() / user_id / "audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    dest = audit_dir / f"{audit.id}.md"
    dest.write_text(minuta_texto, encoding="utf-8")
    audit.minuta_path = str(dest)
    await session.commit()
    await session.refresh(audit)
    return audit


def gravar_romaneio(audit: Audit, romaneio_texto: str) -> None:
    """Escreve o romaneio como par da minuta: `{audit_id}.romaneio.md`.
    Caller chama APÓS gravar_audit (precisa de audit.id e minuta_path).
    """
    from pathlib import Path

    romaneio_path = Path(audit.minuta_path).with_suffix(".romaneio.md")
    romaneio_path.write_text(romaneio_texto, encoding="utf-8")


def ler_minuta(audit: Audit) -> str:
    path = Path(audit.minuta_path)
    if not path.exists():
        raise MinutaNaoEncontrada(audit.minuta_path)
    return path.read_text(encoding="utf-8")


def ler_romaneio(audit: Audit) -> str:
    """Romaneio vive em `{minuta_path sem .md}.romaneio.md`."""
    minuta_path = Path(audit.minuta_path)
    romaneio_path = minuta_path.with_suffix(".romaneio.md")
    if not romaneio_path.exists():
        raise RomaneioNaoEncontrado(str(romaneio_path))
    return romaneio_path.read_text(encoding="utf-8")
