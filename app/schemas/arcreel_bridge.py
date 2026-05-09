from typing import Literal

from pydantic import Field

from app.schemas.common import StrictSchema


class BridgeReferenceImage(StrictSchema):
    file_path: str = Field(min_length=1)
    file_name: str | None = None
    role: str = "reference"
    usage: str = "reference image"


class BridgeImageRequest(StrictSchema):
    backend: Literal["dreamina_cli", "chatgpt_web"]
    prompt: str = Field(min_length=1)
    output_name: str = Field(min_length=1)
    aspect_ratio: str = "9:16"
    reference_images: list[BridgeReferenceImage] = Field(default_factory=list)


class BridgeImageResponse(StrictSchema):
    status: str
    backend: str
    file_path: str | None = None
    submit_id: str | None = None
    provider_raw_response: dict | None = None
    error_message: str | None = None


class BridgeVideoRequest(StrictSchema):
    backend: Literal["dreamina_video_cli"] = "dreamina_video_cli"
    mode: Literal["text2video", "image2video", "multimodal2video", "multiframe2video"] = "text2video"
    prompt: str = Field(min_length=1)
    duration: int = 4
    ratio: str = "16:9"
    video_resolution: str = "720p"
    model_version: str = "seedance2.0"
    reference_images: list[BridgeReferenceImage] = Field(default_factory=list)


class BridgeVideoResponse(StrictSchema):
    status: str
    bridge_job_id: int | None = None
    backend: str
    mode: str
    submit_id: str | None = None
    file_path: str | None = None
    provider_raw_response: dict | None = None
    error_message: str | None = None
    dispatch_status: str | None = None
    queue_name: str | None = None
    dispatch_error: str | None = None
    poll_dispatch_status: str | None = None
    poll_queue_name: str | None = None
    poll_dispatch_error: str | None = None
