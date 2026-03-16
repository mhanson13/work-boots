"""add seo competitor intelligence phase 2a foundations

Revision ID: 0015_seo_competitor_phase2a_foundations
Revises: 0014_seo_sites_uniqueness_hardening
Create Date: 2026-03-16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0015_seo_competitor_phase2a_foundations"
down_revision = "0014_seo_sites_uniqueness_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "seo_competitor_sets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("business_id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("state", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.UniqueConstraint(
            "business_id",
            "site_id",
            "name",
            name="uq_seo_competitor_sets_business_site_name",
        ),
    )
    op.create_index("ix_seo_competitor_sets_business_id", "seo_competitor_sets", ["business_id"], unique=False)
    op.create_index("ix_seo_competitor_sets_site_id", "seo_competitor_sets", ["site_id"], unique=False)
    op.create_index(
        "ix_seo_competitor_sets_business_site_active",
        "seo_competitor_sets",
        ["business_id", "site_id", "is_active"],
        unique=False,
    )
    op.create_index(
        "ix_seo_competitor_sets_business_created_at",
        "seo_competitor_sets",
        ["business_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "seo_competitor_domains",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("business_id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("competitor_set_id", sa.String(length=36), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("base_url", sa.String(length=2048), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="manual"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["competitor_set_id"], ["seo_competitor_sets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "business_id",
            "competitor_set_id",
            "domain",
            name="uq_seo_competitor_domains_business_set_domain",
        ),
    )
    op.create_index("ix_seo_competitor_domains_business_id", "seo_competitor_domains", ["business_id"], unique=False)
    op.create_index("ix_seo_competitor_domains_site_id", "seo_competitor_domains", ["site_id"], unique=False)
    op.create_index(
        "ix_seo_competitor_domains_competitor_set_id",
        "seo_competitor_domains",
        ["competitor_set_id"],
        unique=False,
    )
    op.create_index("ix_seo_competitor_domains_domain", "seo_competitor_domains", ["domain"], unique=False)
    op.create_index(
        "ix_seo_competitor_domains_business_set_active",
        "seo_competitor_domains",
        ["business_id", "competitor_set_id", "is_active"],
        unique=False,
    )
    op.create_index(
        "ix_seo_competitor_domains_business_site",
        "seo_competitor_domains",
        ["business_id", "site_id"],
        unique=False,
    )

    op.create_table(
        "seo_competitor_snapshot_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("business_id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("competitor_set_id", sa.String(length=36), nullable=False),
        sa.Column("client_audit_run_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("max_domains", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("max_pages_per_domain", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("max_depth", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("same_domain_only", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("domains_targeted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("domains_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_attempted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_captured", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors_encountered", sa.Integer(), nullable=False, server_default="0"),
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
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
        sa.ForeignKeyConstraint(["site_id"], ["seo_sites.id"]),
        sa.ForeignKeyConstraint(["competitor_set_id"], ["seo_competitor_sets.id"]),
        sa.ForeignKeyConstraint(["client_audit_run_id"], ["seo_audit_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_seo_competitor_snapshot_runs_business_id",
        "seo_competitor_snapshot_runs",
        ["business_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_competitor_snapshot_runs_site_id",
        "seo_competitor_snapshot_runs",
        ["site_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_competitor_snapshot_runs_competitor_set_id",
        "seo_competitor_snapshot_runs",
        ["competitor_set_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_competitor_snapshot_runs_client_audit_run_id",
        "seo_competitor_snapshot_runs",
        ["client_audit_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_competitor_snapshot_runs_business_set_created_at",
        "seo_competitor_snapshot_runs",
        ["business_id", "competitor_set_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_seo_competitor_snapshot_runs_business_status",
        "seo_competitor_snapshot_runs",
        ["business_id", "status"],
        unique=False,
    )

    op.create_table(
        "seo_competitor_snapshot_pages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("business_id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("competitor_set_id", sa.String(length=36), nullable=False),
        sa.Column("snapshot_run_id", sa.String(length=36), nullable=False),
        sa.Column("competitor_domain_id", sa.String(length=36), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("canonical_url", sa.String(length=2048), nullable=True),
        sa.Column("h1_json", sa.JSON(), nullable=True),
        sa.Column("h2_json", sa.JSON(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("internal_link_count", sa.Integer(), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("error_summary", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["competitor_set_id"], ["seo_competitor_sets.id"]),
        sa.ForeignKeyConstraint(["snapshot_run_id"], ["seo_competitor_snapshot_runs.id"]),
        sa.ForeignKeyConstraint(["competitor_domain_id"], ["seo_competitor_domains.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "business_id",
            "snapshot_run_id",
            "competitor_domain_id",
            "url",
            name="uq_seo_competitor_snapshot_pages_business_run_domain_url",
        ),
    )
    op.create_index(
        "ix_seo_competitor_snapshot_pages_business_id",
        "seo_competitor_snapshot_pages",
        ["business_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_competitor_snapshot_pages_site_id",
        "seo_competitor_snapshot_pages",
        ["site_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_competitor_snapshot_pages_competitor_set_id",
        "seo_competitor_snapshot_pages",
        ["competitor_set_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_competitor_snapshot_pages_snapshot_run_id",
        "seo_competitor_snapshot_pages",
        ["snapshot_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_competitor_snapshot_pages_competitor_domain_id",
        "seo_competitor_snapshot_pages",
        ["competitor_domain_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_competitor_snapshot_pages_business_run",
        "seo_competitor_snapshot_pages",
        ["business_id", "snapshot_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_competitor_snapshot_pages_business_domain",
        "seo_competitor_snapshot_pages",
        ["business_id", "competitor_domain_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_seo_competitor_snapshot_pages_business_domain", table_name="seo_competitor_snapshot_pages")
    op.drop_index("ix_seo_competitor_snapshot_pages_business_run", table_name="seo_competitor_snapshot_pages")
    op.drop_index("ix_seo_competitor_snapshot_pages_competitor_domain_id", table_name="seo_competitor_snapshot_pages")
    op.drop_index("ix_seo_competitor_snapshot_pages_snapshot_run_id", table_name="seo_competitor_snapshot_pages")
    op.drop_index("ix_seo_competitor_snapshot_pages_competitor_set_id", table_name="seo_competitor_snapshot_pages")
    op.drop_index("ix_seo_competitor_snapshot_pages_site_id", table_name="seo_competitor_snapshot_pages")
    op.drop_index("ix_seo_competitor_snapshot_pages_business_id", table_name="seo_competitor_snapshot_pages")
    op.drop_table("seo_competitor_snapshot_pages")

    op.drop_index("ix_seo_competitor_snapshot_runs_business_status", table_name="seo_competitor_snapshot_runs")
    op.drop_index("ix_seo_competitor_snapshot_runs_business_set_created_at", table_name="seo_competitor_snapshot_runs")
    op.drop_index("ix_seo_competitor_snapshot_runs_client_audit_run_id", table_name="seo_competitor_snapshot_runs")
    op.drop_index("ix_seo_competitor_snapshot_runs_competitor_set_id", table_name="seo_competitor_snapshot_runs")
    op.drop_index("ix_seo_competitor_snapshot_runs_site_id", table_name="seo_competitor_snapshot_runs")
    op.drop_index("ix_seo_competitor_snapshot_runs_business_id", table_name="seo_competitor_snapshot_runs")
    op.drop_table("seo_competitor_snapshot_runs")

    op.drop_index("ix_seo_competitor_domains_business_site", table_name="seo_competitor_domains")
    op.drop_index("ix_seo_competitor_domains_business_set_active", table_name="seo_competitor_domains")
    op.drop_index("ix_seo_competitor_domains_domain", table_name="seo_competitor_domains")
    op.drop_index("ix_seo_competitor_domains_competitor_set_id", table_name="seo_competitor_domains")
    op.drop_index("ix_seo_competitor_domains_site_id", table_name="seo_competitor_domains")
    op.drop_index("ix_seo_competitor_domains_business_id", table_name="seo_competitor_domains")
    op.drop_table("seo_competitor_domains")

    op.drop_index("ix_seo_competitor_sets_business_created_at", table_name="seo_competitor_sets")
    op.drop_index("ix_seo_competitor_sets_business_site_active", table_name="seo_competitor_sets")
    op.drop_index("ix_seo_competitor_sets_site_id", table_name="seo_competitor_sets")
    op.drop_index("ix_seo_competitor_sets_business_id", table_name="seo_competitor_sets")
    op.drop_table("seo_competitor_sets")
