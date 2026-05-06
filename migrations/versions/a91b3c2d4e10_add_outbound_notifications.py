"""add outbound notifications

Revision ID: a91b3c2d4e10
Revises: f0d9b8d7a001
Create Date: 2026-05-06 21:15:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "a91b3c2d4e10"
down_revision = "f0d9b8d7a001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "outbound_notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("channel_type", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.String(length=128), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.alter_column("outbound_notifications", "retry_count", server_default=None)


def downgrade():
    op.drop_table("outbound_notifications")
