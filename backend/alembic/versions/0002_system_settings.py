"""system settings

Revision ID: 0002_system_settings
Revises: 86496720a390
Create Date: 2026-10-10 14:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_system_settings"
down_revision: str | None = "86496720a390"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name="uq_system_settings_key"),
    )
    with op.batch_alter_table("system_settings", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_system_settings_key"), ["key"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("system_settings", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_system_settings_key"))

    op.drop_table("system_settings")
