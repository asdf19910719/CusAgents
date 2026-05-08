from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StoryShot(Base):
    __tablename__ = "story_shots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("story_projects.id"), nullable=False)
    shot_index: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    script_text: Mapped[str] = mapped_column(Text, nullable=False)
    visual_description: Mapped[str] = mapped_column(Text, nullable=False)
    camera_motion: Mapped[str] = mapped_column(Text, nullable=False)
    character_names: Mapped[list] = mapped_column(JSON, nullable=False)
    scene_names: Mapped[list] = mapped_column(JSON, nullable=False)
    prop_names: Mapped[list] = mapped_column(JSON, nullable=False)
    duration: Mapped[int] = mapped_column(nullable=False, default=5)
    ratio: Mapped[str] = mapped_column(String(16), nullable=False, default="16:9")
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(32), nullable=True)

    project: Mapped["StoryProject"] = relationship(back_populates="shots")
    images: Mapped[list["StoryShotImage"]] = relationship(back_populates="shot", cascade="all, delete-orphan")
    video_jobs: Mapped[list["StoryShotVideoJob"]] = relationship(
        back_populates="shot", cascade="all, delete-orphan"
    )
