"""add seo deterministic recommendation foundations

Revision ID: 0019_seo_recommendation_foundations
Revises: 0018_seo_competitor_comparison_summaries
Create Date: 2026-03-16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0019_seo_recommendation_foundations"
down_revision = "0018_seo_competitor_comparison_summaries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "seo_recommendation_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("business_id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("audit_run_id", sa.String(length=36), nullable=True),
        sa.Column("comparison_run_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("total_recommendations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("critical_recommendations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warning_recommendations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("info_recommendations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("category_counts_json", sa.JSON(), nullable=True),
        sa.Column("effort_bucket_counts_json", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
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
        sa.CheckConstraint(
            "audit_run_id IS NOT NULL OR comparison_run_id IS NOT NULL",
            name="ck_seo_recommendation_runs_requires_input_lineage",
        ),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
        sa.ForeignKeyConstraint(["site_id"], ["seo_sites.id"]),
        sa.ForeignKeyConstraint(["audit_run_id"], ["seo_audit_runs.id"]),
        sa.ForeignKeyConstraint(["comparison_run_id"], ["seo_competitor_comparison_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_seo_recommendation_runs_business_id",
        "seo_recommendation_runs",
        ["business_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendation_runs_site_id",
        "seo_recommendation_runs",
        ["site_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendation_runs_audit_run_id",
        "seo_recommendation_runs",
        ["audit_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendation_runs_comparison_run_id",
        "seo_recommendation_runs",
        ["comparison_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendation_runs_business_site_created_at",
        "seo_recommendation_runs",
        ["business_id", "site_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendation_runs_business_status",
        "seo_recommendation_runs",
        ["business_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendation_runs_business_audit_run",
        "seo_recommendation_runs",
        ["business_id", "audit_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendation_runs_business_comparison_run",
        "seo_recommendation_runs",
        ["business_id", "comparison_run_id"],
        unique=False,
    )

    op.create_table(
        "seo_recommendations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("business_id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("recommendation_run_id", sa.String(length=36), nullable=False),
        sa.Column("audit_run_id", sa.String(length=36), nullable=True),
        sa.Column("comparison_run_id", sa.String(length=36), nullable=True),
        sa.Column("rule_key", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("effort_bucket", sa.String(length=16), nullable=False, server_default="MEDIUM"),
        sa.Column("evidence_json", sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(["recommendation_run_id"], ["seo_recommendation_runs.id"]),
        sa.ForeignKeyConstraint(["audit_run_id"], ["seo_audit_runs.id"]),
        sa.ForeignKeyConstraint(["comparison_run_id"], ["seo_competitor_comparison_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "business_id",
            "recommendation_run_id",
            "rule_key",
            name="uq_seo_recommendations_business_run_rule_key",
        ),
    )
    op.create_index(
        "ix_seo_recommendations_business_id",
        "seo_recommendations",
        ["business_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_site_id",
        "seo_recommendations",
        ["site_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_recommendation_run_id",
        "seo_recommendations",
        ["recommendation_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_audit_run_id",
        "seo_recommendations",
        ["audit_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_comparison_run_id",
        "seo_recommendations",
        ["comparison_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_rule_key",
        "seo_recommendations",
        ["rule_key"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_severity",
        "seo_recommendations",
        ["severity"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_category",
        "seo_recommendations",
        ["category"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_effort_bucket",
        "seo_recommendations",
        ["effort_bucket"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_business_site_created_at",
        "seo_recommendations",
        ["business_id", "site_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_business_run_priority",
        "seo_recommendations",
        ["business_id", "recommendation_run_id", "priority_score"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_business_severity",
        "seo_recommendations",
        ["business_id", "severity"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_business_category",
        "seo_recommendations",
        ["business_id", "category"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_business_effort",
        "seo_recommendations",
        ["business_id", "effort_bucket"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_seo_recommendations_business_effort", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_business_category", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_business_severity", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_business_run_priority", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_business_site_created_at", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_effort_bucket", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_category", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_severity", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_rule_key", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_comparison_run_id", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_audit_run_id", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_recommendation_run_id", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_site_id", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_business_id", table_name="seo_recommendations")
    op.drop_table("seo_recommendations")

    op.drop_index("ix_seo_recommendation_runs_business_comparison_run", table_name="seo_recommendation_runs")
    op.drop_index("ix_seo_recommendation_runs_business_audit_run", table_name="seo_recommendation_runs")
    op.drop_index("ix_seo_recommendation_runs_business_status", table_name="seo_recommendation_runs")
    op.drop_index("ix_seo_recommendation_runs_business_site_created_at", table_name="seo_recommendation_runs")
    op.drop_index("ix_seo_recommendation_runs_comparison_run_id", table_name="seo_recommendation_runs")
    op.drop_index("ix_seo_recommendation_runs_audit_run_id", table_name="seo_recommendation_runs")
    op.drop_index("ix_seo_recommendation_runs_site_id", table_name="seo_recommendation_runs")
    op.drop_index("ix_seo_recommendation_runs_business_id", table_name="seo_recommendation_runs")
    op.drop_table("seo_recommendation_runs")
