"""LGPD — exportação de dados e anonimização ("direito ao esquecimento").

`anonymize_user` NÃO faz hard-delete. Razão prática: rows de Payment e
StripeEvent precisam ser retidas para reconciliação fiscal/contábil
(NFE, conciliação Stripe, possíveis disputas). FK aponta para o User row
que permanece, mas com PII removida.

O que vira nada:
- email → "deleted-{user_id_prefix}@example.invalid" (formato válido só
  para evitar quebra de constraint NOT NULL + unique; não roteia)
- name → "Conta encerrada"
- oab_numero → "0"; oab_uf → "XX"
- password_hash → "" (login impossível)
- oab_status → REVOKED
- tos_aceito_em → permanece (registro do consentimento histórico)

O que permanece:
- created_at (necessário para análise de cohort agregado)
- Subscription → status CANCELED, plan_code TRIAL, pecas_incluidas=0
- Payments → intactos (obrigação fiscal)
- Audits → metadados retidos; arquivos das minutas DELETADOS do disco
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nexus.db.models import (
    Audit,
    OABStatus,
    Payment,
    PlanCode,
    Subscription,
    SubscriptionStatus,
    User,
)


async def export_user_data(session: AsyncSession, user: User) -> dict:
    """Dump LGPD: tudo que temos do usuário, em JSON serializável.

    Audits voltam só como metadados — texto da minuta cada um baixa pelo
    /user/audits/{id} individualmente (response seria gigante se incluísse
    todos os textos juntos).
    """
    sub_result = await session.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    sub = sub_result.scalar_one_or_none()

    pay_result = await session.execute(
        select(Payment)
        .where(Payment.user_id == user.id)
        .order_by(Payment.created_at.desc())
    )
    payments = pay_result.scalars().all()

    aud_result = await session.execute(
        select(Audit).where(Audit.user_id == user.id).order_by(Audit.created_at.desc())
    )
    audits = aud_result.scalars().all()

    return {
        "exported_at": "now",  # caller pode injetar timestamp se quiser
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "oab_numero": user.oab_numero,
            "oab_uf": user.oab_uf,
            "oab_status": user.oab_status.value,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "tos_aceito_em": user.tos_aceito_em.isoformat() if user.tos_aceito_em else None,
            "tos_version": user.tos_version,
        },
        "subscription": (
            None
            if sub is None
            else {
                "plan_code": sub.plan_code.value,
                "status": sub.status.value,
                "stripe_subscription_id": sub.stripe_subscription_id,
                "current_period_start": sub.current_period_start.isoformat(),
                "current_period_end": sub.current_period_end.isoformat(),
                "pecas_incluidas": sub.pecas_incluidas,
                "pecas_consumidas_no_periodo": sub.pecas_consumidas_no_periodo,
            }
        ),
        "payments": [
            {
                "id": p.id,
                "stripe_invoice_id": p.stripe_invoice_id,
                "amount_cents": p.amount_cents,
                "currency": p.currency,
                "status": p.status.value,
                "created_at": p.created_at.isoformat(),
            }
            for p in payments
        ],
        "audits": [
            {
                "id": a.id,
                "feito_id": a.feito_id,
                "peca_tipo": a.peca_tipo,
                "quality_score": a.quality_score,
                "modelo": a.modelo,
                "created_at": a.created_at.isoformat(),
                "minuta_url": f"/user/audits/{a.id}",
            }
            for a in audits
        ],
    }


async def anonymize_user(session: AsyncSession, user: User) -> None:
    """Anonimização irreversível por solicitação do titular (LGPD art. 18)."""
    short_id = user.id[:8]

    user.email = f"deleted-{short_id}@example.invalid"
    user.name = "Conta encerrada"
    user.oab_numero = "0"
    user.oab_uf = "XX"
    user.password_hash = ""  # login impossível
    user.oab_status = OABStatus.REVOKED
    session.add(user)

    sub_result = await session.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    sub = sub_result.scalar_one_or_none()
    if sub is not None:
        sub.status = SubscriptionStatus.CANCELED
        sub.plan_code = PlanCode.TRIAL
        sub.pecas_incluidas = 0
        session.add(sub)

    # Deletar arquivos físicos das minutas (audit rows permanecem como
    # metadado anônimo). Caminho seguro: usa o minuta_path persistido.
    aud_result = await session.execute(
        select(Audit).where(Audit.user_id == user.id)
    )
    for audit in aud_result.scalars():
        if audit.minuta_path:
            p = Path(audit.minuta_path)
            if p.exists():
                p.unlink()

    # Também removemos o diretório CASO_DATA_DIR/{user_id} se vazio
    caso_dir = os.getenv("CASO_DATA_DIR")
    if caso_dir:
        user_dir = Path(caso_dir) / user.id
        if user_dir.exists():
            # Apaga audits/, deixa eventual feito_id/ (uploads) limpo também
            audits_dir = user_dir / "audits"
            if audits_dir.exists():
                for f in audits_dir.iterdir():
                    if f.is_file():
                        f.unlink()
                audits_dir.rmdir()

    await session.commit()
