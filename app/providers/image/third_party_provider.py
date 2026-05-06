import base64

from app.providers.image.base import BaseImageProvider, ImageGenerationResult


class ThirdPartyImageProvider(BaseImageProvider):
    def __init__(self, client, backend_name="third_party"):
        self.client = client
        self.backend_name = backend_name

    def generate_image(self, shot_index, positive_prompt, negative_prompt, style_preset, seed):
        prompt = positive_prompt
        if style_preset:
            prompt = "Style: {0}\n{1}".format(style_preset, prompt)
        if negative_prompt:
            prompt = "{0}\nAvoid: {1}".format(prompt, negative_prompt)
        payload = {
            "model": self.client.model_name,
            "prompt": prompt,
            "size": "1024x1024",
        }
        response = self.client.create_image(payload)
        image_base64 = response.get("image_base64") or response.get("b64_json")
        if not image_base64:
            data = response.get("data") or []
            if data:
                image_base64 = data[0].get("b64_json") or data[0].get("image_base64")
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
