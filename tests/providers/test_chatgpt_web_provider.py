from pathlib import Path

import pytest

from app.providers.image.chatgpt_web_client import ChatgptWebClient
from app.providers.image.chatgpt_web_provider import ChatgptWebImageProvider


class FakeBrowserRunner:
    def __init__(self, generated_path):
        self.generated_path = generated_path
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return self.generated_path, {"flow": "fake-browser"}


def test_chatgpt_web_provider_reads_generated_file_bytes(tmp_path):
    output_file = tmp_path / "chatgpt-web-shot-1.png"
    output_file.write_bytes(b"fake-chatgpt-web-png")

    class FakeClient:
        def __init__(self):
            self.calls = []

        def generate_image_file(self, prompt, shot_index):
            self.calls.append({"prompt": prompt, "shot_index": shot_index})
            return output_file, {"flow": "fake-browser"}

    client = FakeClient()
    provider = ChatgptWebImageProvider(client=client, backend_name="chatgpt_web")

    result = provider.generate_image(
        shot_index=1,
        positive_prompt="hero in rain",
        negative_prompt="blurry",
        style_preset="cinematic",
        seed=1001,
    )

    assert result.provider_name == "chatgpt_web"
    assert result.image_bytes == b"fake-chatgpt-web-png"
    assert result.file_name == "chatgpt-web-shot-1"
    assert result.file_extension == ".png"
    assert result.metadata["provider_name"] == "chatgpt_web"
    assert client.calls[0]["shot_index"] == 1


def test_chatgpt_web_provider_normalizes_storyboard_instruction_prompt(tmp_path):
    output_file = tmp_path / "chatgpt-web-shot-2.png"
    output_file.write_bytes(b"fake-chatgpt-web-png")

    class FakeClient:
        def __init__(self):
            self.calls = []

        def generate_image_file(self, prompt, shot_index):
            self.calls.append({"prompt": prompt, "shot_index": shot_index})
            return output_file, {"flow": "fake-browser"}

    client = FakeClient()
    provider = ChatgptWebImageProvider(client=client, backend_name="chatgpt_web")

    provider.generate_image(
        shot_index=2,
        positive_prompt=(
            'Create a shot prompt for shot 1.\n'
            'Style preset: "minimal"\n'
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
        seed=1002,
    )

    prompt = client.calls[0]["prompt"]
    assert prompt.startswith("Generate one image now using the image generation tool.")
    assert "Do not answer with text only." in prompt
    assert "Create a shot prompt" not in prompt
    assert "Return positive and negative prompts" not in prompt
    assert "Storyboard frame in minimal style." in prompt
    assert "Close-up of a photograph on a wooden table." in prompt
    assert "Subject: Man's trembling fingers and a photograph of a smiling woman." in prompt
    assert "Avoid: blurry" in prompt


def test_chatgpt_web_client_passes_profile_dir_and_prompt_suffix(tmp_path):
    output_file = tmp_path / "chatgpt-web-generated.png"
    output_file.write_bytes(b"fake-chatgpt-web-png")
    runner = FakeBrowserRunner(output_file)
    client = ChatgptWebClient(
        base_url="https://chatgpt.com/",
        profile_dir=str(tmp_path / "profile"),
        headless=True,
        timeout_seconds=180,
        browser_channel="chrome",
        executable_path="",
        cdp_url="",
        image_prompt_suffix="请直接生成图片并下载 PNG。",
        browser_runner=runner,
    )

    generated_path, metadata = client.generate_image_file(prompt="hero in rain", shot_index=3)

    assert generated_path == output_file
    assert metadata["flow"] == "fake-browser"
    assert runner.calls[0]["base_url"] == "https://chatgpt.com/"
    assert runner.calls[0]["browser_channel"] == "chrome"
    assert runner.calls[0]["cdp_url"] == ""
    assert Path(runner.calls[0]["profile_dir"]).name == "profile"
    assert runner.calls[0]["prompt"].endswith("请直接生成图片并下载 PNG。")


def test_chatgpt_web_client_raises_clear_error_when_browser_flow_returns_missing_file(tmp_path):
    missing_path = tmp_path / "missing.png"
    runner = FakeBrowserRunner(missing_path)
    client = ChatgptWebClient(
        base_url="https://chatgpt.com/",
        profile_dir=str(tmp_path / "profile"),
        browser_runner=runner,
    )

    with pytest.raises(RuntimeError) as exc_info:
        client.generate_image_file(prompt="hero in rain", shot_index=4)

    assert "did not produce expected file" in str(exc_info.value)
