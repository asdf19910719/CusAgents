import json
import re
import subprocess
from pathlib import Path


class DreaminaCliError(RuntimeError):
    def __init__(self, message, submit_id=None, gen_status=None, metadata=None):
        RuntimeError.__init__(self, message)
        self.submit_id = submit_id
        self.gen_status = gen_status
        self.metadata = metadata or {}


class DreaminaCliClient:
    def __init__(
        self,
        cli_path,
        output_dir,
        runner=None,
        poll_seconds=120,
        timeout_seconds=180,
        cwd=".",
    ):
        self.cli_path = cli_path
        self.output_dir = Path(output_dir)
        self.runner = runner or subprocess.run
        self.poll_seconds = int(poll_seconds)
        self.timeout_seconds = int(timeout_seconds)
        self.cwd = cwd

    def generate_image_file(self, prompt, shot_index, ratio, resolution_type, model_version):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        command = self._build_text2image_command(
            prompt=prompt,
            ratio=ratio,
            resolution_type=resolution_type,
            model_version=model_version,
        )
        try:
            result = self.runner(
                command,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            output_text = self._combine_output(exc.output or "", exc.stderr or "")
            metadata = self._parse_output(output_text)
            metadata["command"] = command
            raise DreaminaCliError(
                "dreamina cli text2image timed out after {0} seconds".format(self.timeout_seconds),
                submit_id=metadata.get("submit_id"),
                gen_status=metadata.get("gen_status") or "timeout",
                metadata=metadata,
            ) from exc

        output_text = self._combine_output(result.stdout, result.stderr)
        metadata = self._parse_output(output_text)
        metadata.update(
            {
                "command": command,
                "stdout": result.stdout or "",
                "stderr": result.stderr or "",
                "returncode": result.returncode,
                "poll_seconds": self.poll_seconds,
            }
        )
        if result.returncode != 0:
            raise DreaminaCliError(
                "dreamina cli text2image failed: " + self._classify_error(output_text),
                submit_id=metadata.get("submit_id"),
                gen_status=metadata.get("gen_status"),
                metadata=metadata,
            )

        gen_status = metadata.get("gen_status")
        submit_id = metadata.get("submit_id")
        if gen_status == "fail":
            reason = metadata.get("fail_reason") or self._classify_error(output_text)
            raise DreaminaCliError(
                "dreamina cli text2image failed for submit_id={0}: {1}".format(submit_id, reason),
                submit_id=submit_id,
                gen_status=gen_status,
                metadata=metadata,
            )
        if gen_status == "querying":
            raise DreaminaCliError(
                "dreamina cli text2image task is still querying; submit_id={0}".format(submit_id),
                submit_id=submit_id,
                gen_status=gen_status,
                metadata=metadata,
            )
        if gen_status and gen_status != "success":
            raise DreaminaCliError(
                "dreamina cli text2image returned unsupported gen_status={0}".format(gen_status),
                submit_id=submit_id,
                gen_status=gen_status,
                metadata=metadata,
            )

        generated_path = self._resolve_output_path(metadata)
        if not generated_path and submit_id:
            download_metadata = self.query_result(submit_id=submit_id, download_dir=str(self.output_dir))
            metadata["download_metadata"] = download_metadata
            generated_path = self._resolve_output_path(download_metadata)
        if not generated_path:
            raise DreaminaCliError(
                "dreamina cli text2image did not report generated file path",
                submit_id=submit_id,
                gen_status=gen_status,
                metadata=metadata,
            )
        if not generated_path.exists():
            raise DreaminaCliError(
                "dreamina cli text2image output file not found: " + str(generated_path),
                submit_id=submit_id,
                gen_status=gen_status,
                metadata=metadata,
            )
        return generated_path, metadata

    def query_result(self, submit_id, download_dir=None):
        target_dir = Path(download_dir or self.output_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        command = [
            self.cli_path,
            "query_result",
            "--submit_id",
            submit_id,
            "--download_dir",
            str(target_dir),
        ]
        result = self.runner(
            command,
            cwd=self.cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=self.timeout_seconds,
        )
        output_text = self._combine_output(result.stdout, result.stderr)
        metadata = self._parse_output(output_text)
        metadata.update(
            {
                "command": command,
                "stdout": result.stdout or "",
                "stderr": result.stderr or "",
                "returncode": result.returncode,
            }
        )
        if result.returncode != 0:
            raise DreaminaCliError(
                "dreamina cli query_result failed: " + self._classify_error(output_text),
                submit_id=submit_id,
                gen_status=metadata.get("gen_status"),
                metadata=metadata,
            )
        return metadata

    def _build_text2image_command(self, prompt, ratio, resolution_type, model_version):
        command = [
            self.cli_path,
            "text2image",
            "--prompt",
            prompt,
        ]
        if ratio:
            command.extend(["--ratio", ratio])
        if resolution_type:
            command.extend(["--resolution_type", resolution_type])
        if model_version:
            command.extend(["--model_version", model_version])
        if self.poll_seconds > 0:
            command.extend(["--poll", str(self.poll_seconds)])
        return command

    def _parse_output(self, output_text):
        metadata = {}
        for payload in self._json_candidates(output_text):
            self._merge_json_metadata(metadata, payload)
        fallback_patterns = {
            "submit_id": r"submit_id[\"'\s:=]+([A-Za-z0-9_.:-]+)",
            "gen_status": r"gen_status[\"'\s:=]+([A-Za-z0-9_.:-]+)",
            "fail_reason": r"fail_reason[\"'\s:=]+([^\r\n,}]+)",
            "file_path": r"file_path[\"'\s:=]+(.+?)(?:\r?\n|$)",
            "local_path": r"local_path[\"'\s:=]+(.+?)(?:\r?\n|$)",
            "download_path": r"download_path[\"'\s:=]+(.+?)(?:\r?\n|$)",
        }
        for key, pattern in fallback_patterns.items():
            if key in metadata:
                continue
            match = re.search(pattern, output_text or "", re.IGNORECASE)
            if match:
                metadata[key] = self._clean_text_value(match.group(1))
        if "result_url" not in metadata:
            url_match = re.search(r"https?://\S+", output_text or "")
            if url_match:
                metadata["result_url"] = url_match.group(0).rstrip(".,;")
        return metadata

    def _json_candidates(self, text):
        candidates = []
        stripped = (text or "").strip()
        if not stripped:
            return candidates
        try:
            candidates.append(json.loads(stripped))
            return candidates
        except ValueError:
            pass
        for match in re.finditer(r"\{.*?\}", stripped, re.DOTALL):
            try:
                candidates.append(json.loads(match.group(0)))
            except ValueError:
                continue
        return candidates

    def _merge_json_metadata(self, metadata, payload):
        if not isinstance(payload, dict):
            return
        for key, value in payload.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                metadata[key] = value
        data = payload.get("data")
        if isinstance(data, dict):
            self._merge_json_metadata(metadata, data)
        result_json = payload.get("result_json")
        if isinstance(result_json, dict):
            self._merge_json_metadata(metadata, result_json)
        for key in ("result", "results", "files", "file_paths", "images", "videos"):
            value = payload.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and self._looks_like_media_path(item):
                        metadata.setdefault("file_path", item)
                    elif isinstance(item, dict):
                        self._merge_json_metadata(metadata, item)

    def _resolve_output_path(self, metadata):
        for key in ("file_path", "local_path", "download_path", "path", "output_path"):
            value = metadata.get(key)
            if not value:
                continue
            candidate = Path(str(value).strip().strip('"'))
            if not candidate.is_absolute():
                output_candidate = (self.output_dir / candidate).resolve()
                cwd_candidate = (Path(self.cwd) / candidate).resolve()
                candidate = output_candidate if output_candidate.exists() else cwd_candidate
            return candidate
        return self._find_recent_media_file()

    def _find_recent_media_file(self):
        if not self.output_dir.exists():
            return None
        candidates = [
            path
            for path in self.output_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
        return candidates[0]

    def _looks_like_media_path(self, value):
        lowered = value.lower()
        return lowered.endswith((".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".webm"))

    def _clean_text_value(self, value):
        return str(value).strip().strip('"').strip("'").rstrip(",")

    def _combine_output(self, stdout, stderr):
        return "\n".join([part for part in (stdout or "", stderr or "") if part])

    def _classify_error(self, output_text):
        lowered = (output_text or "").lower()
        if "aigccomplianceconfirmationrequired" in lowered:
            return "compliance_required: complete Dreamina Web authorization first"
        if "credit" in lowered or "insufficient" in lowered:
            return "insufficient_credit: check dreamina user_credit"
        if "login" in lowered or "unauthorized" in lowered:
            return "not_logged_in: run dreamina login or relogin"
        return (output_text or "unknown error").strip()
