from pathlib import Path

from app.services.codex_run_service import CodexRunService


class FakeRunner:
    def __init__(self, stdout="", returncode=0, stderr=""):
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = stderr
        self.calls = []

    def __call__(self, command, cwd, capture_output, text, encoding, errors, check, timeout):
        self.calls.append(
            {
                "command": command,
                "cwd": cwd,
                "timeout": timeout,
            }
        )

        class Result:
            pass

        result = Result()
        result.returncode = self.returncode
        result.stdout = self.stdout
        result.stderr = self.stderr
        return result


def test_codex_run_service_executes_prompt_and_writes_output(tmp_path):
    output_dir = tmp_path / "output"
    runner = FakeRunner(stdout="task finished")
    service = CodexRunService(
        command_name="codex",
        model_name="",
        workdir=str(tmp_path),
        output_dir=str(output_dir),
        runner=runner,
        timeout_seconds=120,
    )

    result = service.execute_run(run_id=11, prompt_text="Summarize blockers")

    assert result["status"] == "completed"
    assert result["result_text"] == "task finished"
    assert Path(result["output_text_path"]).exists()
    assert "exec" in runner.calls[0]["command"]


def test_codex_run_service_collects_generated_images_from_codex_home(tmp_path):
    generated_images_dir = tmp_path / "generated_images" / "session-1"
    source_image = generated_images_dir / "ig_1.png"

    def runner(command, cwd, capture_output, text, encoding, errors, check, timeout):
        generated_images_dir.mkdir(parents=True, exist_ok=True)
        source_image.write_bytes(b"fake-image")

        class Result:
            pass

        result = Result()
        result.returncode = 0
        result.stdout = "done"
        result.stderr = ""
        return result

    service = CodexRunService(
        command_name="codex",
        model_name="",
        workdir=str(tmp_path),
        output_dir=str(tmp_path / "output"),
        runner=runner,
        timeout_seconds=120,
        generated_images_dir=str(tmp_path / "generated_images"),
    )

    result = service.execute_run(run_id=12, prompt_text="Generate an image")

    assert result["status"] == "completed"
    assert len(result["image_paths"]) == 1
    assert Path(result["image_paths"][0]).exists()
