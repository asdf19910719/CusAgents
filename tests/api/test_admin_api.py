from fastapi.testclient import TestClient

from app.main import app
from app.api.routes.admin import get_conversation_service
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


def test_admin_conversations_endpoint_returns_conversation_overviews():
    class FakeConversationService:
        def list_session_overviews(self, session, limit=20):
            return [
                {
                    "session_id": 7,
                    "chat_id": "oc_test_chat",
                    "status": "active",
                    "started_at": "2026-05-07T10:00:00",
                    "last_message_at": "2026-05-07T10:05:00",
                    "closed_at": None,
                    "close_reason": None,
                    "active_message_count": 4,
                    "compacted_message_count": 8,
                    "has_summary": True,
                    "latest_summary_text": "summary",
                    "source_run_ids": [3, 4],
                }
            ]

    app.dependency_overrides[get_conversation_service] = lambda: FakeConversationService()
    client = TestClient(app)

    try:
        response = client.get("/admin/conversations?limit=5")
    finally:
        app.dependency_overrides.pop(get_conversation_service, None)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["session_id"] == 7
    assert payload[0]["active_message_count"] == 4
    assert payload[0]["source_run_ids"] == [3, 4]


def test_admin_conversation_cleanup_endpoint_returns_cleanup_result():
    class FakeConversationService:
        def cleanup_sessions(self, session, now=None, retention_seconds=None, batch_size=None):
            return {
                "expired_session_count": 2,
                "deleted_session_count": 3,
                "deleted_message_count": 9,
                "detached_run_count": 1,
                "retention_seconds": retention_seconds,
                "batch_size": batch_size,
            }

    app.dependency_overrides[get_conversation_service] = lambda: FakeConversationService()
    client = TestClient(app)

    try:
        response = client.post("/admin/conversations/cleanup?retention_seconds=7200&batch_size=25")
    finally:
        app.dependency_overrides.pop(get_conversation_service, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["expired_session_count"] == 2
    assert payload["deleted_session_count"] == 3
    assert payload["deleted_message_count"] == 9
    assert payload["detached_run_count"] == 1
    assert payload["retention_seconds"] == 7200
    assert payload["batch_size"] == 25
