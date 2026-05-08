from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StoryShotVideoJob(Base):
    __tablename__ = "story_shot_video_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("story_projects.id"), nullable=False)
    shot_id: Mapped[int] = mapped_column(ForeignKey("story_shots.id"), nullable=False)
    video_job_id: Mapped[int] = mapped_column(ForeignKey("video_jobs.id"), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    submit_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    reference_manifest_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    started_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(32), nullable=True)

    project: Mapped["StoryProject"] = relationship(back_populates="shot_video_jobs")
    shot: Mapped["StoryShot"] = relationship(back_populates="video_jobs")
    video_job: Mapped["VideoJob"] = relationship()
