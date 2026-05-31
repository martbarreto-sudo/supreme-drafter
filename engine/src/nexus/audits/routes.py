"""Rotas /user/audits — histórico do advogado autenticado."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nexus.auth.deps import get_current_user
from nexus.db.models import Audit, User
from nexus.db.session import get_session

from .schemas import AuditDetail, AuditSummary
from .service import MinutaNaoEncontrada, ler_minuta

router = APIRouter(prefix="/user/audits", tags=["audits"])


def _summary(a: Audit) -> AuditSummary:
    return AuditSummary(
        id=a.id,
        feito_id=a.feito_id,
        peca_tipo=a.peca_tipo,
        quality_score=a.quality_score,
        modelo=a.modelo,
        created_at=a.created_at,
    )


@router.get("", response_model=list[AuditSummary])
async def list_audits(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[AuditSummary]:
    result = await session.execute(
        select(Audit)
        .where(Audit.user_id == user.id)
        .order_by(Audit.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [_summary(a) for a in result.scalars()]


@router.get("/{audit_id}", response_model=AuditDetail)
async def get_audit(
    audit_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AuditDetail:
    audit = await session.get(Audit, audit_id)
    # Não diferenciar "não existe" vs "não é seu" — sempre 404
    # (não vaza informação sobre IDs de outros usuários)
    if audit is None or audit.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Auditoria não encontrada")
    try:
        minuta = ler_minuta(audit)
    except MinutaNaoEncontrada:
        raise HTTPException(
            status.HTTP_410_GONE, "Arquivo da minuta não está mais disponível"
        )
    return AuditDetail(
        id=audit.id,
        feito_id=audit.feito_id,
        peca_tipo=audit.peca_tipo,
        quality_score=audit.quality_score,
        modelo=audit.modelo,
        created_at=audit.created_at,
        minuta=minuta,
        usage={
            "input_tokens": audit.input_tokens,
            "cache_read_tokens": audit.cache_read_tokens,
            "cache_creation_tokens": audit.cache_creation_tokens,
            "output_tokens": audit.output_tokens,
        },
    )
