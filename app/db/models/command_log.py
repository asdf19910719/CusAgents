from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CommandLog(Base):
    __tablename__ = "command_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    channel_type: Mapped[str] = mapped_column(String(32), nullable=False)
    sender_id: Mapped[str] = mapped_column(String(128), nullable=False)
    command_name: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    arguments_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    result_status: Mapped[str] = mapped_column(String(32), nullable=False)
    related_job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id"), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str | None] = mapped_column(String(32), nullable=True)

    job: Mapped["Job | None"] = relationship()
