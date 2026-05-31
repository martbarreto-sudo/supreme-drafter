"""create subscriptions table

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-31

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: str | None = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "plan_code",
            sa.Enum("TRIAL", "SOLO", "BANCA", "CORPORATE", name="plancode"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "TRIAL", "ACTIVE", "PAST_DUE", "CANCELED",
                name="subscriptionstatus",
            ),
            nullable=False,
        ),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pecas_incluidas", sa.Integer, nullable=False),
        sa.Column("pecas_consumidas_no_periodo", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_subscriptions_user_id", "subscriptions", ["user_id"], unique=True
    )
    op.create_index(
        "ix_subscriptions_stripe_subscription_id",
        "subscriptions",
        ["stripe_subscription_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_subscriptions_stripe_subscription_id", table_name="subscriptions"
    )
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.drop_table("subscriptions")
    op.execute("DROP TYPE IF EXISTS plancode")
    op.execute("DROP TYPE IF EXISTS subscriptionstatus")
