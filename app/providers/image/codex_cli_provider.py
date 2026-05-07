import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from shutil import copyfile
from shutil import which

from app.providers.image.base import BaseImageProvider, ImageGenerationResult


class CodexCliClient:
    def __init__(self, command_name, model_name="", workdir=".", runner=None, generated_images_dir=None):
        self.command_name = command_name
        self.model_name = model_name
        self.workdir = Path(workdir)
        self.runner = runner or subprocess.run
        self._last_materialized_source = ""
        if generated_images_dir:
            self.generated_images_dir = Path(generated_images_dir)
        else:
            codex_home = Path.home() / ".codex"
            self.generated_images_dir = codex_home / "generated_images"

    def generate_image_file(self, prompt, shot_index):
        output_dir = self.workdir / "output" / "codex_cli_tmp"
        output_dir.mkdir(parents=True, exist_ok=True)
        target_path = output_dir / ("codex-cli-shot-{0}.png".format(shot_index))
        last_message_path = output_dir / ("codex-cli-shot-{0}.txt".format(shot_index))
        resolved_command = which(self.command_name) or self.command_name
        known_generated_files = self._list_generated_images()
        started_at = datetime.now()
        full_prompt = prompt + "\nSave the final PNG exactly to: {0}\nReply only with the exact saved file path.".format(
            target_path
        )
        command = [resolved_command, "-a", "never", "-s", "danger-full-access"]
        if self.model_name:
            command.extend(["-m", self.model_name])
        command.extend(
            [
                "exec",
                "-C",
                str(self.workdir),
                "-o",
                str(last_message_path),
                full_prompt,
            ]
        )
        result = self.runner(
            command,
            cwd=str(self.workdir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError("codex cli image generation failed: " + (result.stderr or result.stdout).strip())
        saved_path_text = ""
        if last_message_path.exists():
            saved_path_text = last_message_path.read_text(encoding="utf-8").strip()
        if not saved_path_text:
            output_lines = [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]
            if output_lines:
                saved_path_text = output_lines[-1]
        if not saved_path_text:
            generated_path = self._materialize_generated_image(
                target_path=target_path,
                known_generated_files=known_generated_files,
                started_at=started_at,
            )
            if not generated_path:
                raise RuntimeError("codex cli did not report generated file path")
            saved_path_text = str(generated_path)
        generated_path = Path(saved_path_text)
        if not generated_path.is_absolute():
            generated_path = (self.workdir / generated_path).resolve()
        if not generated_path.exists():
            fallback_generated_path = self._materialize_generated_image(
                target_path=target_path,
                known_generated_files=known_generated_files,
                started_at=started_at,
            )
            if not fallback_generated_path:
                raise RuntimeError("codex cli did not produce expected file: " + str(generated_path))
            generated_path = fallback_generated_path
        metadata = {
            "command_name": self.command_name,
            "resolved_command": resolved_command,
            "model_name": self.model_name,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "prompt": full_prompt,
            "target_path": str(target_path),
            "last_message_path": str(last_message_path),
        }
        if generated_path == target_path and self._last_materialized_source:
            metadata["source_generated_image"] = self._last_materialized_source
        return generated_path, metadata

    def _list_generated_images(self):
        if not self.generated_images_dir.exists():
            return set()
        return {str(path.resolve()) for path in self.generated_images_dir.rglob("*") if self._is_image_file(path)}

    def _materialize_generated_image(self, target_path, known_generated_files, started_at):
        newest_image = self._find_newest_generated_image(known_generated_files, started_at)
        if not newest_image:
            return None
        copyfile(str(newest_image), str(target_path))
        self._last_materialized_source = str(newest_image)
        return target_path

    def _find_newest_generated_image(self, known_generated_files, started_at):
        if not self.generated_images_dir.exists():
            return None
        threshold = started_at - timedelta(seconds=5)
        candidates = []
        for path in self.generated_images_dir.rglob("*"):
            if not self._is_image_file(path):
                continue
            resolved_path = str(path.resolve())
            if resolved_path in known_generated_files:
                continue
            if datetime.fromtimestamp(path.stat().st_mtime) < threshold:
                continue
            candidates.append(path)
        if not candidates:
            return None
        candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
        return candidates[0]

    def _is_image_file(self, path):
        return path.is_file() and path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")


class CodexCliImageProvider(BaseImageProvider):
    def __init__(self, client, backend_name="codex_cli"):
        self.client = client
        self.backend_name = backend_name

    def generate_image(self, shot_index, positive_prompt, negative_prompt, style_preset, seed):
        prompt = self._build_prompt(
            shot_index=shot_index,
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            style_preset=style_preset,
            seed=seed,
        )
        generated_path, metadata = self.client.generate_image_file(prompt=prompt, shot_index=shot_index)
        return ImageGenerationResult(
            provider_name=self.backend_name,
            remote_job_id=None,
            image_bytes=generated_path.read_bytes(),
            file_name="codex-cli-shot-{0}".format(shot_index),
            file_extension=generated_path.suffix or ".png",
            metadata={
                "provider_name": self.backend_name,
                "generated_path": str(generated_path),
                "request_prompt": prompt,
                "client_metadata": metadata,
            },
        )

    def _build_prompt(self, shot_index, positive_prompt, negative_prompt, style_preset, seed):
        lines = ["Use the built-in image generation capability, not Python, SVG, HTML, or external APIs."]
        lines.append("Generate a PNG image for storyboard shot {0}.".format(shot_index))
        if style_preset:
            lines.append("Style preset: {0}.".format(style_preset))
        lines.append("Primary prompt: {0}.".format(positive_prompt.rstrip(".")))
        if negative_prompt:
            lines.append("Avoid: {0}.".format(negative_prompt.rstrip(".")))
        lines.append("Preferred seed reference: {0}.".format(seed))
        return " ".join(lines)
