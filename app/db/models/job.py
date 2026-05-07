from decimal import Decimal

from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    style_preset: Mapped[str] = mapped_column(String(100), nullable=False)
    target_shot_count: Mapped[int] = mapped_column(nullable=False)
    image_backend: Mapped[str] = mapped_column(String(64), nullable=False, default="comfyui_remote")
    notification_target_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    current_step: Mapped[str] = mapped_column(String(64), nullable=False)
    total_input_tokens: Mapped[int] = mapped_column(default=0, nullable=False)
    total_output_tokens: Mapped[int] = mapped_column(default=0, nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0.0000"), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(32), nullable=True)

    step_runs: Mapped[list["StepRun"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    assets: Mapped[list["Asset"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    notifications: Mapped[list["OutboundNotification"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
