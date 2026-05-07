from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CodexRun(Base):
    __tablename__ = "codex_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    channel_type: Mapped[str] = mapped_column(String(32), nullable=False)
    sender_id: Mapped[str] = mapped_column(String(128), nullable=False)
    notification_target_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    result_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_text_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_paths_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
