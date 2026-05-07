"""add notification target to jobs

Revision ID: d4c7f61a2b11
Revises: b82a6dd91321
Create Date: 2026-05-07 15:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "d4c7f61a2b11"
down_revision = "b82a6dd91321"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.add_column(sa.Column("notification_target_id", sa.String(length=128), nullable=True))


def downgrade():
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.drop_column("notification_target_id")
