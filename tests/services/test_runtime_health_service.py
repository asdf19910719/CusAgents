from app.core.config import Settings
from app.services.runtime_health_service import RuntimeHealthService


class FakeResult:
    def scalar(self):
        return 1


class FakeSession:
    def execute(self, statement):
        return FakeResult()


def test_runtime_health_service_reports_reachable_backends():
    settings = Settings(
        LLM_API_KEY="real-key",
        LLM_BASE_URL="https://llm.example.com/v1",
        REDIS_URL="redis://127.0.0.1:6379/0",
        AUTO_ENQUEUE_JOBS=True,
        COMFYUI_BASE_URL="http://192.168.1.20:8188",
        IMAGE_BACKEND="comfyui_remote",
        THIRD_PARTY_IMAGE_BASE_URL="https://image.example.com",
        THIRD_PARTY_IMAGE_API_KEY="image-key",
        THIRD_PARTY_IMAGE_MODEL="vendor-model",
    )

    service = RuntimeHealthService(
        settings=settings,
        redis_ping=lambda url: {"status": "ok", "detail": url},
        tcp_check=lambda url: {"status": "ok", "detail": url},
    )

    result = service.collect(FakeSession())

    assert result["status"] == "ok"
    assert result["checks"]["database"]["status"] == "ok"
    assert result["checks"]["redis"]["status"] == "ok"
    assert result["checks"]["llm"]["status"] == "configured"
    assert result["checks"]["image_backends"]["default_backend"] == "comfyui_remote"
    assert result["checks"]["image_backends"]["items"]["comfyui_remote"]["status"] == "ok"
    assert result["checks"]["image_backends"]["items"]["third_party"]["status"] == "ok"


def test_runtime_health_service_marks_missing_or_unreachable_dependencies():
    settings = Settings(
        LLM_API_KEY="placeholder-llm-api-key",
        LLM_BASE_URL="https://llm.example.com/v1",
        REDIS_URL="redis://127.0.0.1:6379/0",
        AUTO_ENQUEUE_JOBS=False,
        COMFYUI_BASE_URL="http://127.0.0.1:8188",
        IMAGE_BACKEND="third_party",
    )

    service = RuntimeHealthService(
        settings=settings,
        redis_ping=lambda url: {"status": "error", "detail": url},
        tcp_check=lambda url: {"status": "error", "detail": url},
    )

    result = service.collect(FakeSession())

    assert result["status"] == "degraded"
    assert result["checks"]["redis"]["enabled"] is False
    assert result["checks"]["redis"]["status"] == "error"
    assert result["checks"]["llm"]["status"] == "missing_config"
    assert result["checks"]["image_backends"]["items"]["comfyui_remote"]["status"] == "error"
    assert result["checks"]["image_backends"]["items"]["third_party"]["status"] == "disabled"
