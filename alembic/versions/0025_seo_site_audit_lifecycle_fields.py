"""add seo site audit lifecycle fields

Revision ID: 0025_seo_site_audit_lifecycle_fields
Revises: 0024_google_business_profile_oauth_connections
Create Date: 2026-03-19
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0025_seo_site_audit_lifecycle_fields"
down_revision = "0024_google_business_profile_oauth_connections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("seo_sites", sa.Column("last_audit_run_id", sa.String(length=36), nullable=True))
    op.add_column("seo_sites", sa.Column("last_audit_status", sa.String(length=32), nullable=True))
    op.add_column("seo_sites", sa.Column("last_audit_completed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("seo_sites", "last_audit_completed_at")
    op.drop_column("seo_sites", "last_audit_status")
    op.drop_column("seo_sites", "last_audit_run_id")
