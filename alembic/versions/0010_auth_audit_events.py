"""add auth admin audit event history table

Revision ID: 0010_auth_audit_events
Revises: 0009_principal_audit_metadata
Create Date: 2026-03-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector


revision = "0010_auth_audit_events"
down_revision = "0009_principal_audit_metadata"
branch_labels = None
depends_on = None


def _table_exists(inspector: Inspector, table: str) -> bool:
    return table in inspector.get_table_names()


def _has_index(inspector: Inspector, table: str, name: str) -> bool:
    for index in inspector.get_indexes(table):
        if index.get("name") == name:
            return True
    return False


def _has_required_columns(inspector: Inspector, table: str, required: set[str]) -> bool:
    existing = {column.get("name") for column in inspector.get_columns(table)}
    return required.issubset(existing)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _table_exists(inspector, "auth_audit_events"):
        op.create_table(
            "auth_audit_events",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("business_id", sa.String(length=36), nullable=False),
            sa.Column("actor_principal_id", sa.String(length=64), nullable=True),
            sa.Column("target_type", sa.String(length=32), nullable=False),
            sa.Column("target_id", sa.String(length=64), nullable=False),
            sa.Column("event_type", sa.String(length=64), nullable=False),
            sa.Column("details_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        required_columns = {"id", "business_id", "target_type", "target_id", "event_type", "details_json", "created_at"}
        if not _has_required_columns(inspector, "auth_audit_events", required_columns):
            raise RuntimeError(
                "Migration 0010 found existing auth_audit_events table with unexpected shape; "
                "local database reset is required."
            )

    inspector = sa.inspect(bind)
    if not _has_index(inspector, "auth_audit_events", "ix_auth_audit_events_business_id"):
        op.create_index("ix_auth_audit_events_business_id", "auth_audit_events", ["business_id"], unique=False)
    if not _has_index(inspector, "auth_audit_events", "ix_auth_audit_events_target_type"):
        op.create_index("ix_auth_audit_events_target_type", "auth_audit_events", ["target_type"], unique=False)
    if not _has_index(inspector, "auth_audit_events", "ix_auth_audit_events_event_type"):
        op.create_index("ix_auth_audit_events_event_type", "auth_audit_events", ["event_type"], unique=False)
    if not _has_index(inspector, "auth_audit_events", "ix_auth_audit_events_target_id"):
        op.create_index("ix_auth_audit_events_target_id", "auth_audit_events", ["target_id"], unique=False)
    if not _has_index(inspector, "auth_audit_events", "ix_auth_audit_events_created_at"):
        op.create_index("ix_auth_audit_events_created_at", "auth_audit_events", ["created_at"], unique=False)
    if not _has_index(inspector, "auth_audit_events", "ix_auth_audit_events_business_created_at"):
        op.create_index(
            "ix_auth_audit_events_business_created_at",
            "auth_audit_events",
            ["business_id", "created_at"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _table_exists(inspector, "auth_audit_events"):
        return
    if _has_index(inspector, "auth_audit_events", "ix_auth_audit_events_business_created_at"):
        op.drop_index("ix_auth_audit_events_business_created_at", table_name="auth_audit_events")
    if _has_index(inspector, "auth_audit_events", "ix_auth_audit_events_created_at"):
        op.drop_index("ix_auth_audit_events_created_at", table_name="auth_audit_events")
    if _has_index(inspector, "auth_audit_events", "ix_auth_audit_events_target_id"):
        op.drop_index("ix_auth_audit_events_target_id", table_name="auth_audit_events")
    if _has_index(inspector, "auth_audit_events", "ix_auth_audit_events_event_type"):
        op.drop_index("ix_auth_audit_events_event_type", table_name="auth_audit_events")
    if _has_index(inspector, "auth_audit_events", "ix_auth_audit_events_target_type"):
        op.drop_index("ix_auth_audit_events_target_type", table_name="auth_audit_events")
    if _has_index(inspector, "auth_audit_events", "ix_auth_audit_events_business_id"):
        op.drop_index("ix_auth_audit_events_business_id", table_name="auth_audit_events")
    op.drop_table("auth_audit_events")
