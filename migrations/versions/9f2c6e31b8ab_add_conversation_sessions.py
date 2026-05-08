"""add conversation sessions

Revision ID: 9f2c6e31b8ab
Revises: e6c3a4b1f902
Create Date: 2026-05-07 18:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "9f2c6e31b8ab"
down_revision = "e6c3a4b1f902"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "conversation_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.String(length=32), nullable=True),
        sa.Column("last_message_at", sa.String(length=32), nullable=True),
        sa.Column("closed_at", sa.String(length=32), nullable=True),
        sa.Column("close_reason", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.Column("updated_at", sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversation_sessions_chat_id"), "conversation_sessions", ["chat_id"], unique=False)
    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_run_id", sa.Integer(), nullable=True),
        sa.Column("is_compacted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.Column("updated_at", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["conversation_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversation_messages_session_id"), "conversation_messages", ["session_id"], unique=False)
    op.add_column("codex_runs", sa.Column("conversation_session_id", sa.Integer(), nullable=True))
    op.add_column("codex_runs", sa.Column("resolved_prompt_text", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_codex_runs_conversation_session_id",
        "codex_runs",
        "conversation_sessions",
        ["conversation_session_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("fk_codex_runs_conversation_session_id", "codex_runs", type_="foreignkey")
    op.drop_column("codex_runs", "resolved_prompt_text")
    op.drop_column("codex_runs", "conversation_session_id")
    op.drop_index(op.f("ix_conversation_messages_session_id"), table_name="conversation_messages")
    op.drop_table("conversation_messages")
    op.drop_index(op.f("ix_conversation_sessions_chat_id"), table_name="conversation_sessions")
    op.drop_table("conversation_sessions")
