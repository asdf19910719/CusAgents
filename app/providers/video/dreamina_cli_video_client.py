from pathlib import Path

from app.providers.image.dreamina_cli_client import DreaminaCliClient, DreaminaCliError


class DreaminaCliVideoClient(DreaminaCliClient):
    def generate_video_file(
        self,
        prompt,
        duration,
        ratio,
        video_resolution,
        model_version,
        mode="text2video",
        image_paths=None,
    ):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        command = self._build_video_command(
            prompt=prompt,
            duration=duration,
            ratio=ratio,
            video_resolution=video_resolution,
            model_version=model_version,
            mode=mode,
            image_paths=image_paths or [],
        )
        result = self._run_command(command)
        metadata = self._parse_output(self._combine_output(result.stdout, result.stderr))
        metadata.update(
            {
                "command": command,
                "stdout": result.stdout or "",
                "stderr": result.stderr or "",
                "returncode": result.returncode,
                "poll_seconds": self.poll_seconds,
            }
        )
        self._raise_for_video_result(result, metadata)
        generated_path = self._resolve_video_output_path(metadata)
        if not generated_path:
            raise DreaminaCliError(
                "dreamina cli {0} did not report generated file path".format(mode),
                submit_id=metadata.get("submit_id"),
                gen_status=metadata.get("gen_status"),
                metadata=metadata,
            )
        if not generated_path.exists():
            raise DreaminaCliError(
                "dreamina cli {0} output file not found: {1}".format(mode, generated_path),
                submit_id=metadata.get("submit_id"),
                gen_status=metadata.get("gen_status"),
                metadata=metadata,
            )
        return generated_path, metadata

    def _run_command(self, command):
        import subprocess

        try:
            return self.runner(
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
            metadata = self._parse_output(self._combine_output(exc.output or "", exc.stderr or ""))
            metadata["command"] = command
            raise DreaminaCliError(
                "dreamina cli text2video timed out after {0} seconds".format(self.timeout_seconds),
                submit_id=metadata.get("submit_id"),
                gen_status=metadata.get("gen_status") or "timeout",
                metadata=metadata,
            ) from exc

    def _build_text2video_command(self, prompt, duration, ratio, video_resolution, model_version):
        command = [
            self.cli_path,
            "text2video",
            "--prompt",
            prompt,
            "--duration",
            str(duration),
        ]
        if ratio:
            command.extend(["--ratio", ratio])
        if video_resolution:
            command.extend(["--video_resolution", video_resolution])
        if model_version:
            command.extend(["--model_version", model_version])
        if self.poll_seconds > 0:
            command.extend(["--poll", str(self.poll_seconds)])
        return command

    def _build_video_command(self, prompt, duration, ratio, video_resolution, model_version, mode, image_paths):
        if mode == "text2video":
            return self._build_text2video_command(prompt, duration, ratio, video_resolution, model_version)
        if mode == "image2video":
            if len(image_paths) != 1:
                raise DreaminaCliError("image2video requires exactly one image")
            command = [self.cli_path, "image2video", "--image", image_paths[0], "--prompt", prompt]
        elif mode == "multimodal2video":
            if len(image_paths) < 2:
                raise DreaminaCliError("multimodal2video requires at least two images")
            command = [self.cli_path, "multimodal2video"]
            for image_path in image_paths:
                command.extend(["--image", image_path])
            command.extend(["--prompt", prompt])
        elif mode == "multiframe2video":
            if len(image_paths) < 2:
                raise DreaminaCliError("multiframe2video requires at least two images")
            command = [self.cli_path, "multiframe2video"]
            for image_path in image_paths:
                command.extend(["--image", image_path])
            command.extend(["--prompt", prompt])
        else:
            raise DreaminaCliError("unsupported dreamina video mode: {0}".format(mode))
        command.extend(["--duration", str(duration)])
        if ratio:
            command.extend(["--ratio", ratio])
        if video_resolution:
            command.extend(["--video_resolution", video_resolution])
        if model_version:
            command.extend(["--model_version", model_version])
        if self.poll_seconds > 0:
            command.extend(["--poll", str(self.poll_seconds)])
        return command

    def _raise_for_video_result(self, result, metadata):
        output_text = self._combine_output(result.stdout, result.stderr)
        submit_id = metadata.get("submit_id")
        gen_status = metadata.get("gen_status")
        if result.returncode != 0:
            raise DreaminaCliError(
                "dreamina cli text2video failed: " + self._classify_error(output_text),
                submit_id=submit_id,
                gen_status=gen_status,
                metadata=metadata,
            )
        if gen_status == "fail":
            raise DreaminaCliError(
                "dreamina cli text2video failed for submit_id={0}: {1}".format(
                    submit_id,
                    metadata.get("fail_reason") or self._classify_error(output_text),
                ),
                submit_id=submit_id,
                gen_status=gen_status,
                metadata=metadata,
            )
        if gen_status == "querying":
            raise DreaminaCliError(
                "dreamina cli text2video task is still querying; submit_id={0}".format(submit_id),
                submit_id=submit_id,
                gen_status=gen_status,
                metadata=metadata,
            )
        if gen_status and gen_status != "success":
            raise DreaminaCliError(
                "dreamina cli text2video returned unsupported gen_status={0}".format(gen_status),
                submit_id=submit_id,
                gen_status=gen_status,
                metadata=metadata,
            )

    def _resolve_video_output_path(self, metadata):
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
        if not self.output_dir.exists():
            return None
        candidates = [
            path
            for path in self.output_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in (".mp4", ".mov", ".webm")
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
        return candidates[0]
