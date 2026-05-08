from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StoryShotImage(Base):
    __tablename__ = "story_shot_images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("story_projects.id"), nullable=False)
    shot_id: Mapped[int] = mapped_column(ForeignKey("story_shots.id"), nullable=False)
    image_asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id"), nullable=True)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    image_type: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(32), nullable=True)

    project: Mapped["StoryProject"] = relationship(back_populates="shot_images")
    shot: Mapped["StoryShot"] = relationship(back_populates="images")
