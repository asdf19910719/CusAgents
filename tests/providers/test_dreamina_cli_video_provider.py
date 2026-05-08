import pytest

from app.providers.image.dreamina_cli_client import DreaminaCliError
from app.providers.video.base import VideoGenerationRequest
from app.providers.video.dreamina_cli_video_client import DreaminaCliVideoClient
from app.providers.video.dreamina_cli_video_provider import DreaminaCliVideoProvider


class FakeRunner:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.calls = []

    def __call__(self, command, cwd, capture_output, text, encoding, errors, check, timeout):
        self.calls.append({"command": command, "cwd": cwd, "timeout": timeout})

        class Result:
            pass

        result = Result()
        result.stdout = self.stdout
        result.stderr = self.stderr
        result.returncode = self.returncode
        return result


def test_dreamina_video_client_invokes_text2video_and_returns_output_path(tmp_path):
    generated_file = tmp_path / "dreamina-video.mp4"
    generated_file.write_bytes(b"fake-mp4")
    runner = FakeRunner(
        stdout=(
            '{"submit_id":"video-submit-1","gen_status":"success",'
            '"file_path":"' + str(generated_file).replace("\\", "\\\\") + '"}'
        )
    )
    client = DreaminaCliVideoClient(
        cli_path="dreamina",
        output_dir=str(tmp_path),
        runner=runner,
        poll_seconds=9,
        timeout_seconds=40,
    )

    generated_path, metadata = client.generate_video_file(
        prompt="cinematic city sunrise",
        duration=4,
        ratio="16:9",
        video_resolution="720p",
        model_version="seedance2.0",
    )

    command = runner.calls[0]["command"]
    assert generated_path == generated_file
    assert command[:2] == ["dreamina", "text2video"]
    assert "--duration" in command
    assert "4" in command
    assert "--video_resolution" in command
    assert "720p" in command
    assert "--model_version" in command
    assert "seedance2.0" in command
    assert "--poll" in command
    assert "9" in command
    assert metadata["submit_id"] == "video-submit-1"


def test_dreamina_video_provider_reads_generated_file_bytes(tmp_path):
    generated_file = tmp_path / "dreamina-video.mp4"
    generated_file.write_bytes(b"fake-mp4")

    class FakeClient:
        def __init__(self):
            self.calls = []

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
            self.calls.append(
                {
                    "prompt": prompt,
                    "duration": duration,
                    "ratio": ratio,
                    "video_resolution": video_resolution,
                    "model_version": model_version,
                    "mode": mode,
                    "image_paths": image_paths,
                }
            )
            return generated_file, {"submit_id": "video-submit-2", "gen_status": "success"}

    client = FakeClient()
    provider = DreaminaCliVideoProvider(
        client=client,
        backend_name="dreamina_video_cli",
        duration=5,
        ratio="16:9",
        video_resolution="720p",
        model_version="seedance2.0",
    )

    result = provider.generate_video(prompt="city sunrise")

    assert result.provider_name == "dreamina_video_cli"
    assert result.remote_job_id == "video-submit-2"
    assert result.video_bytes == b"fake-mp4"
    assert result.file_name == "dreamina-video-cli"
    assert result.file_extension == ".mp4"
    assert result.metadata["submit_id"] == "video-submit-2"
    assert client.calls[0]["duration"] == 5


def test_dreamina_video_provider_defaults_to_seedance2(tmp_path):
    generated_file = tmp_path / "dreamina-video.mp4"
    generated_file.write_bytes(b"fake-mp4")

    class FakeClient:
        def __init__(self):
            self.calls = []

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
            self.calls.append(
                {
                    "prompt": prompt,
                    "duration": duration,
                    "ratio": ratio,
                    "video_resolution": video_resolution,
                    "model_version": model_version,
                    "mode": mode,
                    "image_paths": image_paths,
                }
            )
            return generated_file, {"submit_id": "video-submit-default", "gen_status": "success"}

    client = FakeClient()
    provider = DreaminaCliVideoProvider(client=client)

    provider.generate_video(prompt="city sunrise")

    assert client.calls[0]["model_version"] == "seedance2.0"


def test_dreamina_video_client_raises_querying_with_submit_id(tmp_path):
    runner = FakeRunner(stdout="submit_id: video-submit-3\ngen_status: querying\n")
    client = DreaminaCliVideoClient(cli_path="dreamina", output_dir=str(tmp_path), runner=runner)

    with pytest.raises(DreaminaCliError) as exc_info:
        client.generate_video_file(
            prompt="city sunrise",
            duration=4,
            ratio="16:9",
            video_resolution="720p",
            model_version="seedance2.0",
        )

    assert exc_info.value.submit_id == "video-submit-3"
    assert exc_info.value.gen_status == "querying"


def test_dreamina_video_client_invokes_image2video_for_single_image(tmp_path):
    generated_file = tmp_path / "dreamina-image-video.mp4"
    generated_file.write_bytes(b"fake-mp4")
    runner = FakeRunner(
        stdout=(
            '{"submit_id":"image-video-submit","gen_status":"success",'
            '"file_path":"' + str(generated_file).replace("\\", "\\\\") + '"}'
        )
    )
    client = DreaminaCliVideoClient(cli_path="dreamina", output_dir=str(tmp_path), runner=runner)

    generated_path, _metadata = client.generate_video_file(
        prompt="image based video",
        duration=5,
        ratio="16:9",
        video_resolution="720p",
        model_version="seedance2.0",
        mode="image2video",
        image_paths=["output/shot-001.png"],
    )

    command = runner.calls[0]["command"]
    assert generated_path == generated_file
    assert command[:2] == ["dreamina", "image2video"]
    assert "--image" in command
    assert "output/shot-001.png" in command


def test_dreamina_video_client_invokes_multimodal2video_for_multiple_images(tmp_path):
    generated_file = tmp_path / "dreamina-multimodal-video.mp4"
    generated_file.write_bytes(b"fake-mp4")
    runner = FakeRunner(
        stdout=(
            '{"submit_id":"multimodal-submit","gen_status":"success",'
            '"file_path":"' + str(generated_file).replace("\\", "\\\\") + '"}'
        )
    )
    client = DreaminaCliVideoClient(cli_path="dreamina", output_dir=str(tmp_path), runner=runner)

    client.generate_video_file(
        prompt="multi image video",
        duration=5,
        ratio="16:9",
        video_resolution="720p",
        model_version="seedance2.0",
        mode="multimodal2video",
        image_paths=["output/shot-001.png", "output/hero.png"],
    )

    command = runner.calls[0]["command"]
    assert command[:2] == ["dreamina", "multimodal2video"]
    assert command.count("--image") == 2
    assert "output/shot-001.png" in command
    assert "output/hero.png" in command


def test_dreamina_video_provider_routes_structured_request(tmp_path):
    generated_file = tmp_path / "dreamina-routed-video.mp4"
    generated_file.write_bytes(b"fake-mp4")

    class FakeClient:
        def __init__(self):
            self.calls = []

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
            self.calls.append(
                {
                    "prompt": prompt,
                    "duration": duration,
                    "ratio": ratio,
                    "video_resolution": video_resolution,
                    "model_version": model_version,
                    "mode": mode,
                    "image_paths": image_paths,
                }
            )
            return generated_file, {"submit_id": "routed-submit", "gen_status": "success"}

    client = FakeClient()
    provider = DreaminaCliVideoProvider(client=client)
    request = VideoGenerationRequest(
        prompt="prompt with references",
        mode="multimodal2video",
        reference_images=["output/shot-001.png", "output/hero.png"],
        duration=6,
        ratio="16:9",
        video_resolution="720p",
        model_version="seedance2.0",
        reference_image_usages=[{"file_name": "hero.png", "usage": "主角参考"}],
    )

    result = provider.generate_video(request)

    assert result.metadata["mode"] == "multimodal2video"
    assert client.calls[0]["mode"] == "multimodal2video"
    assert client.calls[0]["image_paths"] == ["output/shot-001.png", "output/hero.png"]
    assert result.metadata["reference_image_usages"][0]["file_name"] == "hero.png"
