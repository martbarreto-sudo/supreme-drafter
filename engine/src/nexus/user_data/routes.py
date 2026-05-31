"""Endpoints LGPD: exportação de dados (art. 18 II) e exclusão (art. 18 VI)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from nexus.auth.deps import get_current_user
from nexus.db.models import User
from nexus.db.session import get_session

from .service import anonymize_user, export_user_data

router = APIRouter(prefix="/user/me", tags=["lgpd"])


@router.get("/export")
async def get_user_data_export(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """LGPD art. 18 II — direito de acesso aos dados.

    Retorna JSON portável com profile + subscription + payments + audits
    (metadados). Texto de cada minuta vem via /user/audits/{id}.
    """
    data = await export_user_data(session, user)
    data["exported_at"] = datetime.now(timezone.utc).isoformat()
    return data


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_account(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """LGPD art. 18 VI — anonimização da conta a pedido do titular.

    Operação irreversível: anonimiza User, cancela assinatura, deleta
    arquivos das minutas. Payment rows permanecem (obrigação fiscal).
    JWT do usuário fica inutilizado (password_hash vazio + status REVOKED).
    """
    await anonymize_user(session, user)
    return None
