"""add minimal principal roles for business-scoped authorization

Revision ID: 0007_principal_roles
Revises: 0006_principals
Create Date: 2026-03-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector


revision = "0007_principal_roles"
down_revision = "0006_principals"
branch_labels = None
depends_on = None


def _has_column(inspector: Inspector, table: str, column: str) -> bool:
    return any(item.get("name") == column for item in inspector.get_columns(table))


def _column_type_name(inspector: Inspector, table: str, column: str) -> str | None:
    for item in inspector.get_columns(table):
        if item.get("name") != column:
            continue
        type_obj = item.get("type")
        if type_obj is None:
            return None
        # SQLAlchemy types expose one or more of name/enum name depending on backend.
        for attr in ("name", "enum_name"):
            value = getattr(type_obj, attr, None)
            if isinstance(value, str) and value:
                return value.lower()
        rendered = str(type_obj).strip().lower()
        return rendered or None
    return None


def _postgres_enum_labels(bind: sa.engine.Connection, enum_name: str) -> list[str]:
    rows = bind.execute(
        sa.text(
            """
            SELECT e.enumlabel
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = :enum_name
            ORDER BY e.enumsortorder
            """
        ),
        {"enum_name": enum_name},
    ).fetchall()
    return [str(row[0]) for row in rows]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    role_enum = sa.Enum("admin", "operator", name="principalrole")
    role_enum.create(bind, checkfirst=True)

    if not _has_column(inspector, "principals", "role"):
        with op.batch_alter_table("principals") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "role",
                    role_enum,
                    nullable=False,
                    server_default=sa.text("'admin'"),
                )
            )
    else:
        role_type_name = _column_type_name(inspector, "principals", "role")
        if bind.dialect.name == "postgresql":
            if role_type_name != "principalrole":
                raise RuntimeError(
                    "Migration 0007 found principals.role already present with unexpected type. "
                    f"Expected principalrole, found {role_type_name!r}."
                )
            enum_labels = _postgres_enum_labels(bind, "principalrole")
            if enum_labels == ["ADMIN", "OPERATOR"]:
                # Drifted local schemas created via ORM metadata may have uppercase enum labels.
                bind.execute(sa.text("ALTER TYPE principalrole RENAME VALUE 'ADMIN' TO 'admin'"))
                bind.execute(sa.text("ALTER TYPE principalrole RENAME VALUE 'OPERATOR' TO 'operator'"))
            elif enum_labels != ["admin", "operator"]:
                raise RuntimeError(
                    "Migration 0007 found existing principalrole enum labels that do not match "
                    f"expected values: {enum_labels!r}."
                )

    with op.batch_alter_table("principals") as batch_op:
        batch_op.alter_column("role", nullable=False, server_default=sa.text("'operator'"))


def downgrade() -> None:
    with op.batch_alter_table("principals") as batch_op:
        batch_op.drop_column("role")

    role_enum = sa.Enum("admin", "operator", name="principalrole")
    role_enum.drop(op.get_bind(), checkfirst=True)
