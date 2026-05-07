import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from shutil import copyfile, which


class CodexRunService:
    def __init__(
        self,
        command_name,
        model_name="",
        workdir=".",
        output_dir="./output/codex_runs",
        runner=None,
        timeout_seconds=300,
        generated_images_dir=None,
    ):
        self.command_name = command_name
        self.model_name = model_name
        self.workdir = Path(workdir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.runner = runner or subprocess.run
        self.timeout_seconds = timeout_seconds
        if generated_images_dir:
            self.generated_images_dir = Path(generated_images_dir)
        else:
            self.generated_images_dir = Path.home() / ".codex" / "generated_images"

    def execute_run(self, run_id, prompt_text):
        text_path = self.output_dir / ("codex-run-{0}.txt".format(run_id))
        known_generated_files = self._list_generated_images()
        started_at = datetime.now()
        command = [which(self.command_name) or self.command_name, "-a", "never", "-s", "danger-full-access"]
        if self.model_name:
            command.extend(["-m", self.model_name])
        command.extend(["exec", "-C", str(self.workdir), "-o", str(text_path), prompt_text])
        result = self.runner(
            command,
            cwd=str(self.workdir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=self.timeout_seconds,
        )
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "codex run failed").strip())
        if not text_path.exists():
            text_path.write_text(result.stdout or "", encoding="utf-8")
        result_text = text_path.read_text(encoding="utf-8").strip()
        image_paths = self._materialize_generated_images(run_id, known_generated_files, started_at)
        return {
            "status": "completed",
            "result_text": result_text or (result.stdout or "").strip(),
            "output_text_path": str(text_path),
            "image_paths": [str(path) for path in image_paths],
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def _list_generated_images(self):
        if not self.generated_images_dir.exists():
            return set()
        return {str(path.resolve()) for path in self.generated_images_dir.rglob("*") if self._is_image_file(path)}

    def _materialize_generated_images(self, run_id, known_generated_files, started_at):
        if not self.generated_images_dir.exists():
            return []
        threshold = started_at - timedelta(seconds=5)
        results = []
        index = 1
        for path in sorted(self.generated_images_dir.rglob("*"), key=lambda item: item.stat().st_mtime):
            if not self._is_image_file(path):
                continue
            resolved = str(path.resolve())
            if resolved in known_generated_files:
                continue
            if datetime.fromtimestamp(path.stat().st_mtime) < threshold:
                continue
            target_path = self.output_dir / ("codex-run-{0}-{1}{2}".format(run_id, index, path.suffix.lower()))
            copyfile(str(path), str(target_path))
            results.append(target_path)
            index += 1
        return results

    def _is_image_file(self, path):
        return path.is_file() and path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")

    @staticmethod
    def encode_image_paths(image_paths):
        return json.dumps(image_paths, ensure_ascii=False)

    @staticmethod
    def decode_image_paths(image_paths_json):
        if not image_paths_json:
            return []
        return json.loads(image_paths_json)
