import re

from app.providers.image.base import BaseImageProvider, ImageGenerationResult


class ChatgptWebImageProvider(BaseImageProvider):
    def __init__(self, client, backend_name="chatgpt_web"):
        self.client = client
        self.backend_name = backend_name

    def generate_image(self, shot_index, positive_prompt, negative_prompt, style_preset, seed):
        visual_prompt = self._normalize_prompt(positive_prompt, style_preset)
        lines = [
            "Generate one image now using the image generation tool.",
            "Do not answer with text only.",
            "Create a single finished PNG image for storyboard shot {0}.".format(shot_index),
            "Visual brief: {0}".format(visual_prompt),
        ]
        if negative_prompt:
            lines.append("Avoid: {0}".format(negative_prompt))
        lines.append("Seed reference: {0}".format(seed))
        prompt = "\n".join(lines)
        generated_path, metadata = self.client.generate_image_file(prompt=prompt, shot_index=shot_index)
        return ImageGenerationResult(
            provider_name=self.backend_name,
            remote_job_id=None,
            image_bytes=generated_path.read_bytes(),
            file_name="chatgpt-web-shot-{0}".format(shot_index),
            file_extension=generated_path.suffix or ".png",
            metadata={
                "provider_name": self.backend_name,
                "generated_path": str(generated_path),
                "request_prompt": prompt,
                "client_metadata": metadata,
            },
        )

    def _normalize_prompt(self, positive_prompt, style_preset):
        source_text = (positive_prompt or "").strip()
        if not source_text:
            return "Create a clean storyboard frame."
        extracted = self._extract_structured_fields(source_text)
        if not extracted:
            if style_preset:
                return "Storyboard frame in {0} style.\n{1}".format(style_preset, source_text)
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
        if len(prompt) > 1200:
            prompt = prompt[:1200].rstrip() + "."
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
