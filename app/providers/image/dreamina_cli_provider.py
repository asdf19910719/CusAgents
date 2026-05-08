import re

from app.providers.image.base import BaseImageProvider, ImageGenerationResult


class DreaminaCliImageProvider(BaseImageProvider):
    def __init__(
        self,
        client,
        backend_name="dreamina_cli",
        ratio="16:9",
        resolution_type="2k",
        model_version="5.0",
    ):
        self.client = client
        self.backend_name = backend_name
        self.ratio = ratio
        self.resolution_type = resolution_type
        self.model_version = model_version

    def generate_image(self, shot_index, positive_prompt, negative_prompt, style_preset, seed):
        prompt = self._build_prompt(
            shot_index=shot_index,
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            style_preset=style_preset,
            seed=seed,
        )
        generated_path, metadata = self.client.generate_image_file(
            prompt=prompt,
            shot_index=shot_index,
            ratio=self.ratio,
            resolution_type=self.resolution_type,
            model_version=self.model_version,
        )
        submit_id = metadata.get("submit_id")
        return ImageGenerationResult(
            provider_name=self.backend_name,
            remote_job_id=submit_id,
            image_bytes=generated_path.read_bytes(),
            file_name="dreamina-cli-shot-{0}".format(shot_index),
            file_extension=generated_path.suffix or ".png",
            metadata={
                "provider_name": self.backend_name,
                "submit_id": submit_id,
                "gen_status": metadata.get("gen_status"),
                "generated_path": str(generated_path),
                "request_prompt": prompt,
                "model_version": self.model_version,
                "ratio": self.ratio,
                "resolution_type": self.resolution_type,
                "client_metadata": metadata,
            },
        )

    def _build_prompt(self, shot_index, positive_prompt, negative_prompt, style_preset, seed):
        visual_prompt = self._normalize_prompt(positive_prompt, style_preset)
        lines = [
            "Create one polished image for storyboard shot {0}.".format(shot_index),
            "Visual brief: {0}".format(visual_prompt),
        ]
        if negative_prompt:
            lines.append("Avoid: {0}".format(negative_prompt))
        lines.append("Seed reference: {0}".format(seed))
        return "\n".join(lines)

    def _normalize_prompt(self, positive_prompt, style_preset):
        source_text = (positive_prompt or "").strip()
        if not source_text:
            return "Create a clean storyboard frame."
        extracted = self._extract_structured_fields(source_text)
        if not extracted:
            if style_preset:
                return "Storyboard frame in {0} style. {1}".format(style_preset, source_text)
            return source_text
        segments = []
        if style_preset:
            segments.append("Storyboard frame in {0} style.".format(style_preset))
        for label, key in (
            ("Scene", "scene"),
            ("Subject", "subject"),
            ("Action", "action"),
            ("Camera", "camera"),
            ("Lighting", "lighting"),
            ("Mood", "emotion"),
        ):
            value = extracted.get(key)
            if value:
                segments.append("{0}: {1}.".format(label, value.rstrip(".")))
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
