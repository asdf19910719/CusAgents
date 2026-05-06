"""add command logs

Revision ID: b82a6dd91321
Revises: a91b3c2d4e10
Create Date: 2026-05-06 23:40:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "b82a6dd91321"
down_revision = "a91b3c2d4e10"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "command_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("channel_type", sa.String(length=32), nullable=False),
        sa.Column("sender_id", sa.String(length=128), nullable=False),
        sa.Column("command_name", sa.String(length=64), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("arguments_json", sa.JSON(), nullable=False),
        sa.Column("result_status", sa.String(length=32), nullable=False),
        sa.Column("related_job_id", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(["related_job_id"], ["jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("command_logs")
