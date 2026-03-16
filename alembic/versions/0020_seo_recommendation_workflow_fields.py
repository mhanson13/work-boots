"""add seo recommendation workflow and prioritization fields

Revision ID: 0020_seo_recommendation_workflow_fields
Revises: 0019_seo_recommendation_foundations
Create Date: 2026-03-16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0020_seo_recommendation_workflow_fields"
down_revision = "0019_seo_recommendation_foundations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "seo_recommendations",
        sa.Column("priority_band", sa.String(length=16), nullable=False, server_default="medium"),
    )
    op.add_column(
        "seo_recommendations",
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
    )
    op.add_column(
        "seo_recommendations",
        sa.Column("decision", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "seo_recommendations",
        sa.Column("decision_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "seo_recommendations",
        sa.Column("assigned_principal_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "seo_recommendations",
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "seo_recommendations",
        sa.Column("snoozed_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "seo_recommendations",
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "seo_recommendations",
        sa.Column("updated_by_principal_id", sa.String(length=64), nullable=True),
    )

    op.execute(
        """
        UPDATE seo_recommendations
        SET priority_band = CASE
            WHEN priority_score >= 90 THEN 'critical'
            WHEN priority_score >= 75 THEN 'high'
            WHEN priority_score >= 50 THEN 'medium'
            ELSE 'low'
        END
        """
    )

    op.create_check_constraint(
        "ck_seo_recommendations_status",
        "seo_recommendations",
        "status IN ('open', 'in_progress', 'accepted', 'dismissed', 'snoozed', 'resolved')",
    )
    op.create_check_constraint(
        "ck_seo_recommendations_decision",
        "seo_recommendations",
        "decision IS NULL OR decision IN ('accept', 'dismiss', 'snooze', 'resolve', 'reopen', 'start')",
    )
    op.create_check_constraint(
        "ck_seo_recommendations_priority_band",
        "seo_recommendations",
        "priority_band IN ('low', 'medium', 'high', 'critical')",
    )

    op.create_foreign_key(
        "fk_seo_recommendations_business_assigned_principal",
        "seo_recommendations",
        "principals",
        ["business_id", "assigned_principal_id"],
        ["business_id", "id"],
    )

    op.create_index(
        "ix_seo_recommendations_status",
        "seo_recommendations",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_decision",
        "seo_recommendations",
        ["decision"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_assigned_principal_id",
        "seo_recommendations",
        ["assigned_principal_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_priority_band",
        "seo_recommendations",
        ["priority_band"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_business_site_status_priority",
        "seo_recommendations",
        ["business_id", "site_id", "status", "priority_score"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_business_priority_band",
        "seo_recommendations",
        ["business_id", "priority_band"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_business_assigned_principal",
        "seo_recommendations",
        ["business_id", "assigned_principal_id"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_business_due_at",
        "seo_recommendations",
        ["business_id", "due_at"],
        unique=False,
    )
    op.create_index(
        "ix_seo_recommendations_business_snoozed_until",
        "seo_recommendations",
        ["business_id", "snoozed_until"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_seo_recommendations_business_snoozed_until", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_business_due_at", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_business_assigned_principal", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_business_priority_band", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_business_site_status_priority", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_priority_band", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_assigned_principal_id", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_decision", table_name="seo_recommendations")
    op.drop_index("ix_seo_recommendations_status", table_name="seo_recommendations")

    op.drop_constraint(
        "fk_seo_recommendations_business_assigned_principal",
        "seo_recommendations",
        type_="foreignkey",
    )
    op.drop_constraint("ck_seo_recommendations_priority_band", "seo_recommendations", type_="check")
    op.drop_constraint("ck_seo_recommendations_decision", "seo_recommendations", type_="check")
    op.drop_constraint("ck_seo_recommendations_status", "seo_recommendations", type_="check")

    op.drop_column("seo_recommendations", "updated_by_principal_id")
    op.drop_column("seo_recommendations", "resolved_at")
    op.drop_column("seo_recommendations", "snoozed_until")
    op.drop_column("seo_recommendations", "due_at")
    op.drop_column("seo_recommendations", "assigned_principal_id")
    op.drop_column("seo_recommendations", "decision_reason")
    op.drop_column("seo_recommendations", "decision")
    op.drop_column("seo_recommendations", "status")
    op.drop_column("seo_recommendations", "priority_band")
