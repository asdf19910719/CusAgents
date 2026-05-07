from pathlib import Path

from app.providers.image.codex_cli_provider import CodexCliClient, CodexCliImageProvider


class FakeRunner:
    def __init__(self, output_text="", returncode=0, stderr=""):
        self.output_text = output_text
        self.returncode = returncode
        self.stderr = stderr
        self.calls = []

    def __call__(self, command, cwd, capture_output, text, check, **kwargs):
        self.calls.append(
            {
                "command": command,
                "cwd": cwd,
                "capture_output": capture_output,
                "text": text,
                "check": check,
                "kwargs": kwargs,
            }
        )

        class Result:
            pass

        result = Result()
        result.returncode = self.returncode
        result.stdout = self.output_text
        result.stderr = self.stderr
        return result


def test_codex_cli_client_invokes_codex_exec_and_returns_output_path(tmp_path):
    output_file = tmp_path / "generated.png"
    output_file.write_bytes(b"fake-png")
    runner = FakeRunner(output_text=str(output_file))
    client = CodexCliClient(
        command_name="codex",
        model_name="",
        workdir=str(tmp_path),
        runner=runner,
    )

    generated_path, metadata = client.generate_image_file(
        prompt="generate a test image",
        shot_index=1,
    )

    assert generated_path == output_file
    assert metadata["command_name"] == "codex"
    assert metadata["stdout"] == str(output_file)
    assert runner.calls[0]["command"][0].lower().endswith("codex.cmd")
    assert "exec" in runner.calls[0]["command"]


def test_codex_cli_provider_reads_generated_file_bytes(tmp_path):
    output_file = tmp_path / "generated.png"
    output_file.write_bytes(b"fake-png")
    runner = FakeRunner(output_text=str(output_file))
    client = CodexCliClient(
        command_name="codex",
        model_name="",
        workdir=str(tmp_path),
        runner=runner,
    )
    provider = CodexCliImageProvider(client=client, backend_name="codex_cli")

    result = provider.generate_image(
        shot_index=2,
        positive_prompt="hero in rain",
        negative_prompt="blurry",
        style_preset="cinematic",
        seed=1002,
    )

    assert result.provider_name == "codex_cli"
    assert result.image_bytes == b"fake-png"
    assert result.file_name == "codex-cli-shot-2"
    assert result.file_extension == ".png"
    assert result.metadata["provider_name"] == "codex_cli"


def test_codex_cli_client_falls_back_to_generated_images_directory(tmp_path):
    generated_images_dir = tmp_path / "generated_images" / "session-1"
    generated_file = generated_images_dir / "ig_test.png"

    def runner(command, cwd, capture_output, text, check, **kwargs):
        generated_images_dir.mkdir(parents=True, exist_ok=True)
        generated_file.write_bytes(b"generated-from-codex")

        class Result:
            pass

        result = Result()
        result.returncode = 0
        result.stdout = "not a file path"
        result.stderr = ""
        return result

    client = CodexCliClient(
        command_name="codex",
        model_name="",
        workdir=str(tmp_path),
        runner=runner,
        generated_images_dir=str(tmp_path / "generated_images"),
    )

    generated_path, metadata = client.generate_image_file(
        prompt="generate a test image",
        shot_index=3,
    )

    assert generated_path.exists()
    assert generated_path.read_bytes() == b"generated-from-codex"
    assert "source_generated_image" in metadata
    assert metadata["source_generated_image"].endswith("ig_test.png")
