import base64
import json

import httpx

from app.providers.image.third_party_client import ThirdPartyImageClient
from app.providers.image.third_party_provider import ThirdPartyImageProvider


def build_transport(payload, assertions=None):
    def handler(request):
        assert request.method == "POST"
        if assertions is not None:
            assertions(request)
        return httpx.Response(200, json=payload)

    return httpx.MockTransport(handler)


def test_third_party_provider_generates_image_bytes_from_base64_payload():
    image_bytes = b"fake-third-party-image"
    encoded = base64.b64encode(image_bytes).decode("ascii")
    client = ThirdPartyImageClient(
        base_url="https://example.com",
        api_key="test-key",
        model_name="image-model",
        http_client=httpx.Client(transport=build_transport({"id": "img-1", "image_base64": encoded}), base_url="https://example.com"),
    )
    provider = ThirdPartyImageProvider(client=client, backend_name="third_party")

    result = provider.generate_image(
        shot_index=1,
        positive_prompt="hero in rain",
        negative_prompt="blurry",
        style_preset="cinematic",
        seed=1001,
    )

    assert result.provider_name == "third_party"
    assert result.remote_job_id == "img-1"
    assert result.image_bytes == image_bytes
    assert result.file_extension == ".png"


def test_third_party_provider_supports_openai_style_image_payload_and_response():
    image_bytes = b"openai-style-image"
    encoded = base64.b64encode(image_bytes).decode("ascii")

    def assert_request(request):
        assert request.url.path == "/images/generations"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload["model"] == "gpt-image-2"
        assert "prompt" in payload
        assert "hero in rain" in payload["prompt"]
        assert "cinematic" in payload["prompt"]
        assert "negative_prompt" not in payload

    client = ThirdPartyImageClient(
        base_url="https://example.com",
        api_key="test-key",
        model_name="gpt-image-2",
        api_path="/images/generations",
        http_client=httpx.Client(
            transport=build_transport(
                {
                    "created": 123,
                    "data": [{"b64_json": encoded}],
                },
                assertions=assert_request,
            ),
            base_url="https://example.com",
        ),
    )
    provider = ThirdPartyImageProvider(client=client, backend_name="third_party")

    result = provider.generate_image(
        shot_index=2,
        positive_prompt="hero in rain",
        negative_prompt="blurry",
        style_preset="cinematic",
        seed=1002,
    )

    assert result.provider_name == "third_party"
    assert result.remote_job_id is None
    assert result.image_bytes == image_bytes
    assert result.file_name == "third-party-shot-2"
