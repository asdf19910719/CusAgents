from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class VideoJob(Base):
    __tablename__ = "video_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    backend: Mapped[str] = mapped_column(String(64), nullable=False, default="dreamina_video_cli")
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="text2video")
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    current_step: Mapped[str] = mapped_column(String(64), nullable=False)
    duration: Mapped[int] = mapped_column(nullable=False, default=5)
    ratio: Mapped[str] = mapped_column(String(16), nullable=False, default="16:9")
    video_resolution: Mapped[str] = mapped_column(String(16), nullable=False, default="720p")
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, default="seedance2.0")
    reference_manifest_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    submit_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notification_target_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(32), nullable=True)

    assets: Mapped[list["VideoAsset"]] = relationship(back_populates="video_job", cascade="all, delete-orphan")
    notifications: Mapped[list["OutboundNotification"]] = relationship(
        back_populates="video_job", cascade="all, delete-orphan"
    )
