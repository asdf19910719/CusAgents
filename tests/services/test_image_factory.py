from app.core.config import Settings
from app.providers.image.comfyui_provider import ComfyUIImageProvider
from app.providers.image.codex_cli_provider import CodexCliImageProvider
from app.providers.image.third_party_provider import ThirdPartyImageProvider
from app.services.factory import build_image_providers


def test_build_image_providers_returns_both_registered_backends():
    settings = Settings(
        LLM_API_KEY="test-key",
        IMAGE_BACKEND="comfyui_remote",
        THIRD_PARTY_IMAGE_BASE_URL="https://example.com",
        THIRD_PARTY_IMAGE_API_KEY="image-key",
        THIRD_PARTY_IMAGE_MODEL="image-model",
    )

    providers = build_image_providers(settings)

    assert isinstance(providers["comfyui_remote"], ComfyUIImageProvider)
    assert isinstance(providers["third_party"], ThirdPartyImageProvider)
    assert isinstance(providers["codex_cli"], CodexCliImageProvider)
