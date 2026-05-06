"""add image backend to jobs

Revision ID: f0d9b8d7a001
Revises: 17f3207e99e3
Create Date: 2026-05-06 19:56:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "f0d9b8d7a001"
down_revision = "17f3207e99e3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "jobs",
        sa.Column("image_backend", sa.String(length=64), nullable=False, server_default="comfyui_remote"),
    )
    op.alter_column("jobs", "image_backend", server_default=None)


def downgrade():
    op.drop_column("jobs", "image_backend")
