from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class VideoGenerationResult:
    provider_name: str
    remote_job_id: str | None
    video_bytes: bytes
    file_name: str
    file_extension: str
    metadata: dict[str, Any]
    duration: int
    ratio: str
    video_resolution: str


@dataclass
class VideoGenerationRequest:
    prompt: str
    mode: str = "text2video"
    start_image: str | None = None
    end_image: str | None = None
    reference_images: list[str] | None = None
    reference_image_usages: list[dict[str, Any]] | None = None
    duration: int = 5
    ratio: str = "16:9"
    video_resolution: str = "720p"
    model_version: str = "seedance2.0"
    submit_id: str | None = None

    def image_paths(self):
        paths = []
        if self.start_image:
            paths.append(self.start_image)
        if self.reference_images:
            for image in self.reference_images:
                if image not in paths:
                    paths.append(image)
        if self.end_image and self.end_image not in paths:
            paths.append(self.end_image)
        return paths


class BaseVideoProvider(ABC):
    @abstractmethod
    def generate_video(self, prompt: str) -> VideoGenerationResult:
        raise NotImplementedError
