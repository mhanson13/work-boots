"""add minimal principal roles for business-scoped authorization

Revision ID: 0007_principal_roles
Revises: 0006_principals
Create Date: 2026-03-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0007_principal_roles"
down_revision = "0006_principals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    role_enum = sa.Enum("admin", "operator", name="principalrole")
    role_enum.create(op.get_bind(), checkfirst=True)

    with op.batch_alter_table("principals") as batch_op:
        batch_op.add_column(
            sa.Column(
                "role",
                role_enum,
                nullable=False,
                server_default=sa.text("'admin'"),
            )
        )

    with op.batch_alter_table("principals") as batch_op:
        batch_op.alter_column("role", server_default=sa.text("'operator'"))


def downgrade() -> None:
    with op.batch_alter_table("principals") as batch_op:
        batch_op.drop_column("role")

    role_enum = sa.Enum("admin", "operator", name="principalrole")
    role_enum.drop(op.get_bind(), checkfirst=True)
