import base64
import re

from app.providers.image.base import BaseImageProvider, ImageGenerationResult


class ThirdPartyImageProvider(BaseImageProvider):
    def __init__(self, client, backend_name="third_party"):
        self.client = client
        self.backend_name = backend_name

    def generate_image(self, shot_index, positive_prompt, negative_prompt, style_preset, seed):
        prompt = self._normalize_prompt(positive_prompt, style_preset)
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

    def _normalize_prompt(self, positive_prompt, style_preset):
        source_text = (positive_prompt or "").strip()
        if not source_text:
            return "Create a clean storyboard frame."
        extracted = self._extract_structured_fields(source_text)
        if not extracted:
            if style_preset:
                return "Style: {0}\n{1}".format(style_preset, source_text)
            return source_text
        segments = []
        if style_preset:
            segments.append("Storyboard frame in {0} style.".format(style_preset))
        scene = extracted.get("scene")
        subject = extracted.get("subject")
        action = extracted.get("action")
        camera = extracted.get("camera")
        lighting = extracted.get("lighting")
        emotion = extracted.get("emotion")
        if scene:
            segments.append(scene.rstrip(".") + ".")
        if subject:
            segments.append("Subject: " + subject.rstrip(".") + ".")
        if action:
            segments.append("Action: " + action.rstrip(".") + ".")
        if camera:
            segments.append("Camera: " + camera.rstrip(".") + ".")
        if lighting:
            segments.append("Lighting: " + lighting.rstrip(".") + ".")
        if emotion:
            segments.append("Mood: " + emotion.rstrip(".") + ".")
        prompt = " ".join(segments).strip()
        if len(prompt) > 500:
            prompt = prompt[:500].rstrip() + "."
        return prompt

    def _extract_structured_fields(self, text):
        mapping = {
            "scene": "scene",
            "subject": "subject",
            "action": "action",
            "camera": "camera",
            "lighting": "lighting",
            "emotion": "emotion",
        }
        extracted = {}
        for line in text.splitlines():
            normalized = line.strip()
            if not normalized or ":" not in normalized:
                continue
            key, value = normalized.split(":", 1)
            field_name = mapping.get(key.strip().lower())
            if not field_name:
                continue
            cleaned = value.strip().strip('"').strip()
            cleaned = re.sub(r"\s+", " ", cleaned)
            if cleaned:
                extracted[field_name] = cleaned
        return extracted
