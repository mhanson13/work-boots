"""add crawl max pages used to seo audit runs

Revision ID: 0032_seo_audit_run_crawl_limit_observability
Revises: 0031_business_seo_audit_crawl_page_limit
Create Date: 2026-03-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0032_seo_audit_run_crawl_limit_observability"
down_revision = "0031_business_seo_audit_crawl_page_limit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("seo_audit_runs") as batch_op:
        batch_op.add_column(
            sa.Column(
                "crawl_max_pages_used",
                sa.Integer(),
                nullable=False,
                server_default="25",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("seo_audit_runs") as batch_op:
        batch_op.drop_column("crawl_max_pages_used")
