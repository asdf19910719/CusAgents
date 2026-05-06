import base64

from app.providers.image.base import BaseImageProvider, ImageGenerationResult


class ThirdPartyImageProvider(BaseImageProvider):
    def __init__(self, client, backend_name="third_party"):
        self.client = client
        self.backend_name = backend_name

    def generate_image(self, shot_index, positive_prompt, negative_prompt, style_preset, seed):
        payload = {
            "model": self.client.model_name,
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt,
            "style_preset": style_preset,
            "seed": seed,
            "shot_index": shot_index,
        }
        response = self.client.create_image(payload)
        image_base64 = response.get("image_base64") or response.get("b64_json")
        if not image_base64:
            raise RuntimeError("third-party response missing image_base64")
        image_bytes = base64.b64decode(image_base64)
        remote_job_id = response.get("id") or response.get("job_id")
        file_name = (remote_job_id or "third-party-shot-" + str(shot_index))
        return ImageGenerationResult(
            provider_name=self.backend_name,
            remote_job_id=remote_job_id,
            image_bytes=image_bytes,
            file_name=file_name,
            file_extension=".png",
            metadata={
                "provider_name": self.backend_name,
                "request_payload": payload,
                "response_payload": response,
            },
        )
