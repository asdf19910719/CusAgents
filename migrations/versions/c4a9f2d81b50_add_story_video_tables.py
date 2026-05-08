"""add story video tables

Revision ID: c4a9f2d81b50
Revises: 7a2d4d1a9d10
Create Date: 2026-05-08
"""

from alembic import op
import sqlalchemy as sa


revision = "c4a9f2d81b50"
down_revision = "7a2d4d1a9d10"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "story_projects",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("request_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("style_prompt", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_stage", sa.String(length=64), nullable=False),
        sa.Column("notification_target_id", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.Column("updated_at", sa.String(length=32), nullable=True),
    )
    op.create_table(
        "story_reference_assets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("story_projects.id"), nullable=False),
        sa.Column("asset_type", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("image_asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=True),
        sa.Column("file_path", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.Column("updated_at", sa.String(length=32), nullable=True),
    )
    op.create_table(
        "story_shots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("story_projects.id"), nullable=False),
        sa.Column("shot_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("script_text", sa.Text(), nullable=False),
        sa.Column("visual_description", sa.Text(), nullable=False),
        sa.Column("camera_motion", sa.Text(), nullable=False),
        sa.Column("character_names", sa.JSON(), nullable=False),
        sa.Column("scene_names", sa.JSON(), nullable=False),
        sa.Column("prop_names", sa.JSON(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("ratio", sa.String(length=16), nullable=False, server_default="16:9"),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.Column("updated_at", sa.String(length=32), nullable=True),
    )
    op.create_table(
        "story_shot_images",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("story_projects.id"), nullable=False),
        sa.Column("shot_id", sa.Integer(), sa.ForeignKey("story_shots.id"), nullable=False),
        sa.Column("image_asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=True),
        sa.Column("file_path", sa.String(length=255), nullable=False),
        sa.Column("image_type", sa.String(length=32), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.Column("updated_at", sa.String(length=32), nullable=True),
    )
    op.create_table(
        "story_shot_video_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("story_projects.id"), nullable=False),
        sa.Column("shot_id", sa.Integer(), sa.ForeignKey("story_shots.id"), nullable=False),
        sa.Column("video_job_id", sa.Integer(), sa.ForeignKey("video_jobs.id"), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("submit_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reference_manifest_json", sa.JSON(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.String(length=32), nullable=True),
        sa.Column("finished_at", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.Column("updated_at", sa.String(length=32), nullable=True),
    )
    op.create_table(
        "story_pipeline_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("story_projects.id"), nullable=False),
        sa.Column("run_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("checkpoint_json", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.String(length=32), nullable=True),
        sa.Column("finished_at", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.Column("updated_at", sa.String(length=32), nullable=True),
    )


def downgrade():
    op.drop_table("story_pipeline_runs")
    op.drop_table("story_shot_video_jobs")
    op.drop_table("story_shot_images")
    op.drop_table("story_shots")
    op.drop_table("story_reference_assets")
    op.drop_table("story_projects")
