"""add business_id to lead_events for tenant-scoped event isolation

Revision ID: 0003_lead_events_business_id
Revises: 0002_business_notification_flags
Create Date: 2026-03-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0003_lead_events_business_id"
down_revision = "0002_business_notification_flags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("lead_events") as batch_op:
        batch_op.add_column(sa.Column("business_id", sa.String(length=36), nullable=True))

    # Backfill from lead ownership so existing rows remain tenant-scoped.
    op.execute(
        sa.text(
            """
            UPDATE lead_events
            SET business_id = (
                SELECT leads.business_id
                FROM leads
                WHERE leads.id = lead_events.lead_id
            )
            WHERE business_id IS NULL
            """
        )
    )

    with op.batch_alter_table("lead_events") as batch_op:
        batch_op.alter_column("business_id", existing_type=sa.String(length=36), nullable=False)
        batch_op.create_index("ix_lead_events_business_id", ["business_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_lead_events_business_id_businesses",
            "businesses",
            ["business_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("lead_events") as batch_op:
        batch_op.drop_constraint("fk_lead_events_business_id_businesses", type_="foreignkey")
        batch_op.drop_index("ix_lead_events_business_id")
        batch_op.drop_column("business_id")
