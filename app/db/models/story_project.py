from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StoryProject(Base):
    __tablename__ = "story_projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    style_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    current_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    notification_target_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(32), nullable=True)

    reference_assets: Mapped[list["StoryReferenceAsset"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    shots: Mapped[list["StoryShot"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    shot_images: Mapped[list["StoryShotImage"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    shot_video_jobs: Mapped[list["StoryShotVideoJob"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    pipeline_runs: Mapped[list["StoryPipelineRun"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
