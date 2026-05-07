from pathlib import Path
import subprocess

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


def test_codex_cli_client_times_out_with_clear_error(tmp_path):
    def runner(command, cwd, capture_output, text, check, **kwargs):
        raise subprocess.TimeoutExpired(cmd=command, timeout=kwargs["timeout"])

    client = CodexCliClient(
        command_name="codex",
        model_name="",
        workdir=str(tmp_path),
        runner=runner,
        timeout_seconds=12,
    )

    try:
        client.generate_image_file(prompt="generate a test image", shot_index=4)
        assert False, "expected timeout"
    except RuntimeError as exc:
        assert "timed out after 12 seconds" in str(exc)


def test_codex_cli_provider_normalizes_storyboard_instruction_prompt(tmp_path):
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

    provider.generate_image(
        shot_index=5,
        positive_prompt=(
            'Create a shot prompt for shot 1.\n'
            'Scene: "Close-up of a photograph on a wooden table"\n'
            'Subject: "Man\'s trembling fingers and a photograph of a smiling woman"\n'
            'Action: "Fingers drift into frame."\n'
            'Camera: "Static close-up"\n'
            'Lighting: "Low-key"\n'
            'Emotion: "Tension"\n'
            'Return positive and negative prompts.'
        ),
        negative_prompt="blurry",
        style_preset="minimal",
        seed=1005,
    )

    prompt = " ".join(runner.calls[0]["command"])
    assert "Create a shot prompt" not in prompt
    assert "Close-up of a photograph on a wooden table" in prompt
    assert "Static close-up" in prompt
