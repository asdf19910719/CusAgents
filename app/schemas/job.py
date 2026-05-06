from typing import Literal

from app.schemas.common import StrictSchema


class JobCreateRequest(StrictSchema):
    topic: str
    style_preset: str
    target_shot_count: int
    image_backend: Literal["comfyui_remote", "third_party"] = "comfyui_remote"
