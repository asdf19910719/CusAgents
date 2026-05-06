import base64

import httpx

from app.providers.image.third_party_client import ThirdPartyImageClient
from app.providers.image.third_party_provider import ThirdPartyImageProvider


def build_transport(payload):
    def handler(request):
        assert request.method == "POST"
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
