import subprocess

import pytest

from app.providers.image.dreamina_cli_client import DreaminaCliClient, DreaminaCliError
from app.providers.image.dreamina_cli_provider import DreaminaCliImageProvider


class FakeRunner:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.calls = []

    def __call__(self, command, cwd, capture_output, text, encoding, errors, check, timeout):
        self.calls.append(
            {
                "command": command,
                "cwd": cwd,
                "capture_output": capture_output,
                "text": text,
                "encoding": encoding,
                "errors": errors,
                "check": check,
                "timeout": timeout,
            }
        )

        class Result:
            pass

        result = Result()
        result.stdout = self.stdout
        result.stderr = self.stderr
        result.returncode = self.returncode
        return result


def test_dreamina_cli_client_invokes_text2image_and_returns_output_path(tmp_path):
    generated_file = tmp_path / "dreamina-shot.png"
    generated_file.write_bytes(b"fake-dreamina-png")
    runner = FakeRunner(
        stdout=(
            '{"submit_id":"submit-1","gen_status":"success",'
            '"file_path":"' + str(generated_file).replace("\\", "\\\\") + '"}'
        )
    )
    client = DreaminaCliClient(
        cli_path="dreamina",
        output_dir=str(tmp_path),
        runner=runner,
        poll_seconds=12,
        timeout_seconds=30,
    )

    generated_path, metadata = client.generate_image_file(
        prompt="a cinematic hero in rain",
        shot_index=1,
        ratio="16:9",
        resolution_type="2k",
        model_version="5.0",
    )

    command = runner.calls[0]["command"]
    assert generated_path == generated_file
    assert command[:2] == ["dreamina", "text2image"]
    assert "--prompt" in command
    assert "--ratio" in command
    assert "16:9" in command
    assert "--resolution_type" in command
    assert "2k" in command
    assert "--model_version" in command
    assert "5.0" in command
    assert "--poll" in command
    assert "12" in command
    assert runner.calls[0]["timeout"] == 30
    assert metadata["submit_id"] == "submit-1"
    assert metadata["gen_status"] == "success"


def test_dreamina_cli_provider_reads_generated_file_bytes(tmp_path):
    generated_file = tmp_path / "dreamina-shot.png"
    generated_file.write_bytes(b"fake-dreamina-png")

    class FakeClient:
        def __init__(self):
            self.calls = []

        def generate_image_file(self, prompt, shot_index, ratio, resolution_type, model_version):
            self.calls.append(
                {
                    "prompt": prompt,
                    "shot_index": shot_index,
                    "ratio": ratio,
                    "resolution_type": resolution_type,
                    "model_version": model_version,
                }
            )
            return generated_file, {"submit_id": "submit-2", "gen_status": "success"}

    client = FakeClient()
    provider = DreaminaCliImageProvider(
        client=client,
        backend_name="dreamina_cli",
        ratio="4:3",
        resolution_type="2k",
        model_version="5.0",
    )

    result = provider.generate_image(
        shot_index=2,
        positive_prompt="hero in rain",
        negative_prompt="blurry",
        style_preset="cinematic",
        seed=1002,
    )

    assert result.provider_name == "dreamina_cli"
    assert result.remote_job_id == "submit-2"
    assert result.image_bytes == b"fake-dreamina-png"
    assert result.file_name == "dreamina-cli-shot-2"
    assert result.file_extension == ".png"
    assert result.metadata["provider_name"] == "dreamina_cli"
    assert result.metadata["submit_id"] == "submit-2"
    assert client.calls[0]["ratio"] == "4:3"
    assert "Avoid: blurry" in client.calls[0]["prompt"]


def test_dreamina_cli_client_raises_clear_error_when_generation_fails(tmp_path):
    runner = FakeRunner(stdout='{"submit_id":"submit-3","gen_status":"fail","fail_reason":"insufficient credit"}')
    client = DreaminaCliClient(cli_path="dreamina", output_dir=str(tmp_path), runner=runner)

    with pytest.raises(DreaminaCliError) as exc_info:
        client.generate_image_file(
            prompt="hero in rain",
            shot_index=3,
            ratio="16:9",
            resolution_type="2k",
            model_version="5.0",
        )

    assert "submit-3" in str(exc_info.value)
    assert "insufficient credit" in str(exc_info.value)
    assert exc_info.value.submit_id == "submit-3"
    assert exc_info.value.gen_status == "fail"


def test_dreamina_cli_client_keeps_submit_id_when_task_is_still_querying(tmp_path):
    runner = FakeRunner(stdout="submit_id: submit-4\ngen_status: querying\n")
    client = DreaminaCliClient(cli_path="dreamina", output_dir=str(tmp_path), runner=runner)

    with pytest.raises(DreaminaCliError) as exc_info:
        client.generate_image_file(
            prompt="hero in rain",
            shot_index=4,
            ratio="16:9",
            resolution_type="2k",
            model_version="5.0",
        )

    assert "still querying" in str(exc_info.value)
    assert exc_info.value.submit_id == "submit-4"
    assert exc_info.value.gen_status == "querying"


def test_dreamina_cli_client_downloads_success_result_when_only_url_is_returned(tmp_path):
    downloaded_file = tmp_path / "submit-url_image_1.png"

    class DownloadingRunner:
        def __init__(self):
            self.calls = []

        def __call__(self, command, cwd, capture_output, text, encoding, errors, check, timeout):
            self.calls.append(command)

            class Result:
                pass

            result = Result()
            result.returncode = 0
            result.stderr = ""
            if command[1] == "text2image":
                result.stdout = (
                    '{"submit_id":"submit-url","gen_status":"success",'
                    '"result_json":{"images":[{"image_url":"https://example.com/image.png"}]}}'
                )
            else:
                downloaded_file.write_bytes(b"downloaded-png")
                result.stdout = (
                    '{"submit_id":"submit-url","gen_status":"success",'
                    '"result_json":{"images":[{"path":"submit-url_image_1.png"}]}}'
                )
            return result

    runner = DownloadingRunner()
    client = DreaminaCliClient(cli_path="dreamina", output_dir=str(tmp_path), runner=runner)

    generated_path, metadata = client.generate_image_file(
        prompt="hero in rain",
        shot_index=6,
        ratio="16:9",
        resolution_type="2k",
        model_version="5.0",
    )

    assert generated_path == downloaded_file
    assert generated_path.read_bytes() == b"downloaded-png"
    assert runner.calls[1][:2] == ["dreamina", "query_result"]
    assert metadata["download_metadata"]["submit_id"] == "submit-url"


def test_dreamina_cli_client_raises_timeout_with_submit_id_when_available(tmp_path):
    class TimeoutRunner:
        def __call__(self, command, cwd, capture_output, text, encoding, errors, check, timeout):
            raise subprocess.TimeoutExpired(cmd=command, timeout=timeout, output="submit_id=submit-5")

    client = DreaminaCliClient(cli_path="dreamina", output_dir=str(tmp_path), runner=TimeoutRunner(), timeout_seconds=7)

    with pytest.raises(DreaminaCliError) as exc_info:
        client.generate_image_file(
            prompt="hero in rain",
            shot_index=5,
            ratio="16:9",
            resolution_type="2k",
            model_version="5.0",
        )

    assert "timed out after 7 seconds" in str(exc_info.value)
    assert exc_info.value.submit_id == "submit-5"
