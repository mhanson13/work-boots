"""add business seo audit crawl page limit setting

Revision ID: 0031_business_seo_audit_crawl_page_limit
Revises: 0030_scpg_observability
Create Date: 2026-03-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0031_business_seo_audit_crawl_page_limit"
down_revision = "0030_scpg_observability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("businesses") as batch_op:
        batch_op.add_column(
            sa.Column(
                "seo_audit_crawl_max_pages",
                sa.Integer(),
                nullable=False,
                server_default="25",
            )
        )
        batch_op.create_check_constraint(
            "ck_businesses_seo_audit_crawl_pages",
            "seo_audit_crawl_max_pages >= 5 AND seo_audit_crawl_max_pages <= 250",
        )


def downgrade() -> None:
    with op.batch_alter_table("businesses") as batch_op:
        batch_op.drop_constraint("ck_businesses_seo_audit_crawl_pages", type_="check")
        batch_op.drop_column("seo_audit_crawl_max_pages")
