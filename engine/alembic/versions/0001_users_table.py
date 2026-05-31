"""create users table

Revision ID: 0001
Revises:
Create Date: 2026-05-31

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: str | None = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("oab_numero", sa.String(10), nullable=False),
        sa.Column("oab_uf", sa.String(2), nullable=False),
        sa.Column(
            "oab_status",
            sa.Enum(
                "PENDING_DECLARATION", "DECLARED", "VERIFIED", "REVOKED",
                name="oabstatus",
            ),
            nullable=False,
            server_default="PENDING_DECLARATION",
        ),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("tos_aceito_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS oabstatus")
