"""add seo phase 1 foundations

Revision ID: 0011_seo_phase1_foundations
Revises: 0010_auth_audit_events
Create Date: 2026-03-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0011_seo_phase1_foundations"
down_revision = "0010_auth_audit_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "seo_sites",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("business_id", sa.String(length=36), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("base_url", sa.String(length=2048), nullable=False),
        sa.Column("normalized_domain", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=128), nullable=True),
        sa.Column("primary_location", sa.String(length=255), nullable=True),
        sa.Column("service_areas_json", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seo_sites_business_id", "seo_sites", ["business_id"], unique=False)
    op.create_index("ix_seo_sites_normalized_domain", "seo_sites", ["normalized_domain"], unique=False)

    op.create_table(
        "seo_audit_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("business_id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_pages", sa.Integer(), nullable=False, server_default="25"),
        sa.Column("max_depth", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("pages_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_crawled", sa.Integer(), nullable=False, server_default="0"),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seo_audit_runs_business_id", "seo_audit_runs", ["business_id"], unique=False)
    op.create_index("ix_seo_audit_runs_site_id", "seo_audit_runs", ["site_id"], unique=False)
    op.create_index("ix_seo_audit_runs_status", "seo_audit_runs", ["status"], unique=False)
    op.create_index(
        "ix_seo_audit_runs_business_site_created_at",
        "seo_audit_runs",
        ["business_id", "site_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "seo_audit_pages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("business_id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("audit_run_id", sa.String(length=36), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("canonical_url", sa.String(length=2048), nullable=True),
        sa.Column("h1_json", sa.JSON(), nullable=True),
        sa.Column("h2_json", sa.JSON(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("internal_link_count", sa.Integer(), nullable=True),
        sa.Column("image_count", sa.Integer(), nullable=True),
        sa.Column("missing_alt_count", sa.Integer(), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
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
    op.create_index("ix_seo_audit_pages_business_id", "seo_audit_pages", ["business_id"], unique=False)
    op.create_index("ix_seo_audit_pages_site_id", "seo_audit_pages", ["site_id"], unique=False)
    op.create_index("ix_seo_audit_pages_audit_run_id", "seo_audit_pages", ["audit_run_id"], unique=False)
    op.create_index(
        "ix_seo_audit_pages_business_run_url",
        "seo_audit_pages",
        ["business_id", "audit_run_id", "url"],
        unique=False,
    )

    op.create_table(
        "seo_audit_findings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("business_id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("audit_run_id", sa.String(length=36), nullable=False),
        sa.Column("page_id", sa.String(length=36), nullable=True),
        sa.Column("finding_type", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("rule_key", sa.String(length=128), nullable=False),
        sa.Column("suggested_fix", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["page_id"], ["seo_audit_pages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seo_audit_findings_business_id", "seo_audit_findings", ["business_id"], unique=False)
    op.create_index("ix_seo_audit_findings_site_id", "seo_audit_findings", ["site_id"], unique=False)
    op.create_index(
        "ix_seo_audit_findings_audit_run_id",
        "seo_audit_findings",
        ["audit_run_id"],
        unique=False,
    )
    op.create_index("ix_seo_audit_findings_page_id", "seo_audit_findings", ["page_id"], unique=False)
    op.create_index(
        "ix_seo_audit_findings_finding_type",
        "seo_audit_findings",
        ["finding_type"],
        unique=False,
    )
    op.create_index("ix_seo_audit_findings_category", "seo_audit_findings", ["category"], unique=False)
    op.create_index("ix_seo_audit_findings_severity", "seo_audit_findings", ["severity"], unique=False)
    op.create_index("ix_seo_audit_findings_rule_key", "seo_audit_findings", ["rule_key"], unique=False)
    op.create_index(
        "ix_seo_audit_findings_business_run_created_at",
        "seo_audit_findings",
        ["business_id", "audit_run_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_seo_audit_findings_business_run_created_at", table_name="seo_audit_findings")
    op.drop_index("ix_seo_audit_findings_rule_key", table_name="seo_audit_findings")
    op.drop_index("ix_seo_audit_findings_severity", table_name="seo_audit_findings")
    op.drop_index("ix_seo_audit_findings_category", table_name="seo_audit_findings")
    op.drop_index("ix_seo_audit_findings_finding_type", table_name="seo_audit_findings")
    op.drop_index("ix_seo_audit_findings_page_id", table_name="seo_audit_findings")
    op.drop_index("ix_seo_audit_findings_audit_run_id", table_name="seo_audit_findings")
    op.drop_index("ix_seo_audit_findings_site_id", table_name="seo_audit_findings")
    op.drop_index("ix_seo_audit_findings_business_id", table_name="seo_audit_findings")
    op.drop_table("seo_audit_findings")

    op.drop_index("ix_seo_audit_pages_business_run_url", table_name="seo_audit_pages")
    op.drop_index("ix_seo_audit_pages_audit_run_id", table_name="seo_audit_pages")
    op.drop_index("ix_seo_audit_pages_site_id", table_name="seo_audit_pages")
    op.drop_index("ix_seo_audit_pages_business_id", table_name="seo_audit_pages")
    op.drop_table("seo_audit_pages")

    op.drop_index("ix_seo_audit_runs_business_site_created_at", table_name="seo_audit_runs")
    op.drop_index("ix_seo_audit_runs_status", table_name="seo_audit_runs")
    op.drop_index("ix_seo_audit_runs_site_id", table_name="seo_audit_runs")
    op.drop_index("ix_seo_audit_runs_business_id", table_name="seo_audit_runs")
    op.drop_table("seo_audit_runs")

    op.drop_index("ix_seo_sites_normalized_domain", table_name="seo_sites")
    op.drop_index("ix_seo_sites_business_id", table_name="seo_sites")
    op.drop_table("seo_sites")
