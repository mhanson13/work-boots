"""add raw output capture to seo competitor profile generation runs

Revision ID: 0029_scpg_run_raw_output
Revises: 0028_seo_competitor_profile_generation_run_retry_lineage
Create Date: 2026-03-21
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0029_scpg_run_raw_output"
down_revision = "0028_seo_competitor_profile_generation_run_retry_lineage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("seo_competitor_profile_generation_runs") as batch_op:
        batch_op.add_column(sa.Column("raw_output", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("seo_competitor_profile_generation_runs") as batch_op:
        batch_op.drop_column("raw_output")
