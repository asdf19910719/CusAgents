from typing import Literal

from app.schemas.common import StrictSchema


class VideoCreateRequest(StrictSchema):
    topic: str | None = None
    prompt: str
    duration: int = 5
    ratio: str = "16:9"
    video_resolution: str = "720p"
    model_version: str = "seedance2.0"
    backend: Literal["dreamina_video_cli"] = "dreamina_video_cli"
    mode: Literal["text2video", "image2video", "multimodal2video", "multiframe2video"] = "text2video"
    reference_manifest_json: dict = {}
