from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ImageGenerationResult:
    provider_name: str
    remote_job_id: str | None
    image_bytes: bytes
    file_name: str
    file_extension: str
    metadata: dict[str, Any]


class BaseImageProvider(ABC):
    @abstractmethod
    def generate_image(
        self,
        shot_index: int,
        positive_prompt: str,
        negative_prompt: str,
        style_preset: str,
        seed: int,
    ) -> ImageGenerationResult:
        raise NotImplementedError
