"""create audits table

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-31

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: str | None = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audits",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("feito_id", sa.String(100), nullable=False),
        sa.Column("peca_tipo", sa.String(20), nullable=False),
        sa.Column("quality_score", sa.Integer, nullable=False),
        sa.Column("modelo", sa.String(50), nullable=False),
        sa.Column("minuta_path", sa.String(500), nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cache_read_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cache_creation_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_audits_user_id", "audits", ["user_id"])
    op.create_index("ix_audits_user_created", "audits", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_audits_user_created", table_name="audits")
    op.drop_index("ix_audits_user_id", table_name="audits")
    op.drop_table("audits")
