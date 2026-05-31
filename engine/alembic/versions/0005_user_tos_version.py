"""add tos_version to users

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-31

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "0005"
down_revision: str | None = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("tos_version", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("users", "tos_version")
