"""add video notification link

Revision ID: 7a2d4d1a9d10
Revises: a91b3c2d4e10
Create Date: 2026-05-08 14:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "7a2d4d1a9d10"
down_revision = "a91b3c2d4e10"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("outbound_notifications") as batch_op:
        batch_op.add_column(sa.Column("video_job_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_outbound_notifications_video_job_id", "video_jobs", ["video_job_id"], ["id"])


def downgrade():
    with op.batch_alter_table("outbound_notifications") as batch_op:
        batch_op.drop_constraint("fk_outbound_notifications_video_job_id", type_="foreignkey")
        batch_op.drop_column("video_job_id")
