"""add business ai prompt text override settings

Revision ID: 0037_business_ai_prompt_text_overrides
Revises: 0036_scpg_tuning_preview_accuracy_events
Create Date: 2026-03-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0037_business_ai_prompt_text_overrides"
down_revision = "0036_scpg_tuning_preview_accuracy_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("businesses") as batch_op:
        batch_op.add_column(sa.Column("ai_prompt_text_competitor", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("ai_prompt_text_recommendations", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("businesses") as batch_op:
        batch_op.drop_column("ai_prompt_text_recommendations")
        batch_op.drop_column("ai_prompt_text_competitor")
