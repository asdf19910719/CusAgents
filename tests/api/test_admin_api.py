from fastapi.testclient import TestClient

from app.main import app
from app.services.runtime_health_service import RuntimeHealthService


def test_admin_endpoints_return_template_and_cost_data():
    client = TestClient(app)

    templates_response = client.get("/admin/templates")
    stats_response = client.get("/admin/stats/cost")

    assert templates_response.status_code == 200
    assert isinstance(templates_response.json(), list)
    assert stats_response.status_code == 200
    assert "total_jobs" in stats_response.json()


def test_admin_runtime_health_endpoint_returns_runtime_report(monkeypatch):
    client = TestClient(app)

    monkeypatch.setattr(
        RuntimeHealthService,
        "collect",
        lambda self, db: {
            "status": "ok",
            "checks": {
                "database": {"status": "ok"},
                "redis": {"status": "ok", "enabled": True},
                "llm": {"status": "configured"},
                "image_backends": {
                    "default_backend": "comfyui_remote",
                    "items": {
                        "comfyui_remote": {"status": "ok"},
                        "third_party": {"status": "disabled"},
                    },
                },
            },
        },
    )

    response = client.get("/admin/runtime/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["checks"]["image_backends"]["items"]["third_party"]["status"] == "disabled"
