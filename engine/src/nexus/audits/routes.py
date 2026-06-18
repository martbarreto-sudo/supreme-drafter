"""Rotas /user/audits — histórico do advogado autenticado."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nexus.auth.deps import get_current_user
from nexus.db.models import Audit, User
from nexus.db.session import get_session

from .schemas import AuditDetail, AuditSummary
from .service import MinutaNaoEncontrada, RomaneioNaoEncontrado, ler_minuta, ler_romaneio

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


@router.get(
    "/{audit_id}/romaneio",
    response_class=PlainTextResponse,
    responses={200: {"content": {"text/markdown": {}}}},
)
async def get_audit_romaneio(
    audit_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PlainTextResponse:
    """Romaneio de Revisão — formato canônico do HITL gate do TIER 0.

    Retorna o markdown classificando a peça como [NIVEL 1 — DISPARAR] ou
    [NIVEL 2 — CONDICIONADA] com as condições a fechar antes do protocolo.
    Gerado em /draft/llm e persistido em disco lado-a-lado com a minuta.
    """
    audit = await session.get(Audit, audit_id)
    if audit is None or audit.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Auditoria não encontrada")
    try:
        texto = ler_romaneio(audit)
    except RomaneioNaoEncontrado:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Romaneio não gerado para esta auditoria (gerado a partir da Fase F)",
        )
    return PlainTextResponse(content=texto, media_type="text/markdown; charset=utf-8")
