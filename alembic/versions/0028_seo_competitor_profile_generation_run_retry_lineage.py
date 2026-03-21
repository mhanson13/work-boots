"""add retry lineage to seo competitor profile generation runs

Revision ID: 0028_seo_competitor_profile_generation_run_retry_lineage
Revises: 0027_seo_competitor_profile_generation_run_queued_status
Create Date: 2026-03-21
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0028_seo_competitor_profile_generation_run_retry_lineage"
down_revision = "0027_seo_competitor_profile_generation_run_queued_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("seo_competitor_profile_generation_runs") as batch_op:
        batch_op.add_column(sa.Column("parent_run_id", sa.String(length=36), nullable=True))
        batch_op.create_index("ix_scpg_runs_parent", ["parent_run_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_scpg_runs_parent_run",
            "seo_competitor_profile_generation_runs",
            ["parent_run_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("seo_competitor_profile_generation_runs") as batch_op:
        batch_op.drop_constraint("fk_scpg_runs_parent_run", type_="foreignkey")
        batch_op.drop_index("ix_scpg_runs_parent")
        batch_op.drop_column("parent_run_id")
