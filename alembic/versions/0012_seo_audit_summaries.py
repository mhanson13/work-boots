"""add seo audit summaries for phase 1 manual ai summarization

Revision ID: 0012_seo_audit_summaries
Revises: 0011_seo_phase1_foundations
Create Date: 2026-03-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0012_seo_audit_summaries"
down_revision = "0011_seo_phase1_foundations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "seo_audit_summaries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("business_id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("audit_run_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="completed"),
        sa.Column("overall_health_summary", sa.Text(), nullable=True),
        sa.Column("top_issues_json", sa.JSON(), nullable=True),
        sa.Column("top_priorities_json", sa.JSON(), nullable=True),
        sa.Column("plain_english_explanation", sa.Text(), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("created_by_principal_id", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
        sa.ForeignKeyConstraint(["site_id"], ["seo_sites.id"]),
        sa.ForeignKeyConstraint(["audit_run_id"], ["seo_audit_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seo_audit_summaries_business_id", "seo_audit_summaries", ["business_id"], unique=False)
    op.create_index("ix_seo_audit_summaries_site_id", "seo_audit_summaries", ["site_id"], unique=False)
    op.create_index("ix_seo_audit_summaries_audit_run_id", "seo_audit_summaries", ["audit_run_id"], unique=False)
    op.create_index(
        "ix_seo_audit_summaries_business_run_version",
        "seo_audit_summaries",
        ["business_id", "audit_run_id", "version"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_seo_audit_summaries_business_run_version", table_name="seo_audit_summaries")
    op.drop_index("ix_seo_audit_summaries_audit_run_id", table_name="seo_audit_summaries")
    op.drop_index("ix_seo_audit_summaries_site_id", table_name="seo_audit_summaries")
    op.drop_index("ix_seo_audit_summaries_business_id", table_name="seo_audit_summaries")
    op.drop_table("seo_audit_summaries")
