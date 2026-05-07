"""add codex runs table

Revision ID: e6c3a4b1f902
Revises: d4c7f61a2b11
Create Date: 2026-05-07 16:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "e6c3a4b1f902"
down_revision = "d4c7f61a2b11"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "codex_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("channel_type", sa.String(length=32), nullable=False),
        sa.Column("sender_id", sa.String(length=128), nullable=False),
        sa.Column("notification_target_id", sa.String(length=128), nullable=True),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result_text", sa.Text(), nullable=True),
        sa.Column("output_text_path", sa.String(length=255), nullable=True),
        sa.Column("image_paths_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.Column("updated_at", sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id"),
    )


def downgrade():
    op.drop_table("codex_runs")
