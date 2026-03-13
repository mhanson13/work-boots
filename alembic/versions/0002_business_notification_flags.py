"""add business notification control flags

Revision ID: 0002_business_notification_flags
Revises: 0001_init
Create Date: 2026-03-12
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0002_business_notification_flags"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("businesses") as batch_op:
        batch_op.add_column(
            sa.Column(
                "customer_auto_ack_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "contractor_alerts_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("businesses") as batch_op:
        batch_op.drop_column("contractor_alerts_enabled")
        batch_op.drop_column("customer_auto_ack_enabled")
