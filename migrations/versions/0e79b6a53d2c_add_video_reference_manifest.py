"""add video reference manifest

Revision ID: 0e79b6a53d2c
Revises: c4a9f2d81b50
Create Date: 2026-05-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0e79b6a53d2c"
down_revision = "c4a9f2d81b50"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "video_jobs",
        sa.Column("reference_manifest_json", sa.JSON(), nullable=False, server_default="{}"),
    )


def downgrade():
    op.drop_column("video_jobs", "reference_manifest_json")
