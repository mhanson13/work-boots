"""allow queued status for seo competitor profile generation runs

Revision ID: 0027_seo_competitor_profile_generation_run_queued_status
Revises: 0026_seo_competitor_profile_generation_drafts
Create Date: 2026-03-21
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0027_seo_competitor_profile_generation_run_queued_status"
down_revision = "0026_seo_competitor_profile_generation_drafts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("seo_competitor_profile_generation_runs") as batch_op:
        batch_op.drop_constraint(
            "ck_seo_competitor_profile_generation_runs_status",
            type_="check",
        )
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=16),
            server_default="queued",
        )
        batch_op.create_check_constraint(
            "ck_seo_competitor_profile_generation_runs_status",
            "status IN ('queued', 'running', 'completed', 'failed')",
        )


def downgrade() -> None:
    with op.batch_alter_table("seo_competitor_profile_generation_runs") as batch_op:
        batch_op.drop_constraint(
            "ck_seo_competitor_profile_generation_runs_status",
            type_="check",
        )
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=16),
            server_default="running",
        )
        batch_op.create_check_constraint(
            "ck_seo_competitor_profile_generation_runs_status",
            "status IN ('running', 'completed', 'failed')",
        )
