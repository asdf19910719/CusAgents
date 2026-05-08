from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class VideoAsset(Base):
    __tablename__ = "video_assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    video_job_id: Mapped[int] = mapped_column(ForeignKey("video_jobs.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    preview_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duration: Mapped[int] = mapped_column(nullable=False)
    ratio: Mapped[str] = mapped_column(String(16), nullable=False)
    video_resolution: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str | None] = mapped_column(String(32), nullable=True)

    video_job: Mapped["VideoJob"] = relationship(back_populates="assets")
