import json

from fastapi.testclient import TestClient

from app.api.routes.jobs import get_job_dispatcher, get_notification_service
from app.api.routes.webhooks import get_command_router
from app.main import app


def test_feishu_url_verification_returns_challenge():
    client = TestClient(app)

    response = client.post(
        "/webhooks/feishu/events",
        json={"type": "url_verification", "challenge": "abc123"},
    )

    assert response.status_code == 200
    assert response.json() == {"challenge": "abc123"}


def test_feishu_event_callback_can_create_job_from_text_command():
    class FakeDispatcher:
        def enqueue_job(self, job_id):
            return {"dispatch_status": "enqueued", "queue_name": "test-queue"}

    class FakeNotificationService:
        def notify_job_event(self, session, job, event_type, message, target_id=None):
            return None

    app.dependency_overrides[get_job_dispatcher] = lambda: FakeDispatcher()
    app.dependency_overrides[get_notification_service] = lambda: FakeNotificationService()
    client = TestClient(app)

    try:
        response = client.post(
            "/webhooks/feishu/events",
            json={
                "type": "event_callback",
                "event": {
                    "sender": {"sender_id": {"open_id": "ou_test_user"}},
                    "message": {
                        "chat_id": "oc_test_chat",
                        "message_type": "text",
                        "content": json.dumps(
                            {
                                "text": '/create topic="赛博 武侠" style=cinematic shots=2 backend=third_party'
                            }
                        ),
                    },
                },
            },
        )
    finally:
        app.dependency_overrides.pop(get_job_dispatcher, None)
        app.dependency_overrides.pop(get_notification_service, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["command_name"] == "create_job"
    assert payload["status"] == "pending"
    assert payload["job_id"] is not None


def test_feishu_event_callback_can_query_job_status():
    class FakeDispatcher:
        def enqueue_job(self, job_id):
            return {"dispatch_status": "enqueued", "queue_name": "test-queue"}

    class FakeNotificationService:
        def notify_job_event(self, session, job, event_type, message, target_id=None):
            return None

    app.dependency_overrides[get_job_dispatcher] = lambda: FakeDispatcher()
    app.dependency_overrides[get_notification_service] = lambda: FakeNotificationService()
    client = TestClient(app)

    try:
        create_response = client.post(
            "/jobs",
            json={
                "topic": "冷血剑客复仇",
                "style_preset": "cinematic",
                "target_shot_count": 1,
                "image_backend": "third_party",
            },
        )
        job_id = create_response.json()["id"]

        response = client.post(
            "/webhooks/feishu/events",
            json={
                "type": "event_callback",
                "event": {
                    "sender": {"sender_id": {"open_id": "ou_test_user"}},
                    "message": {
                        "chat_id": "oc_test_chat",
                        "message_type": "text",
                        "content": json.dumps({"text": "/status job={0}".format(job_id)}),
                    },
                },
            },
        )
    finally:
        app.dependency_overrides.pop(get_job_dispatcher, None)
        app.dependency_overrides.pop(get_notification_service, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["command_name"] == "job_status"
    assert payload["job_id"] == job_id
    assert payload["status"] == "pending"


def test_feishu_event_callback_rejects_invalid_verification_token(monkeypatch):
    monkeypatch.setenv("FEISHU_VERIFICATION_TOKEN", "expected-token")
    client = TestClient(app)

    response = client.post(
        "/webhooks/feishu/events",
        json={
            "type": "event_callback",
            "token": "wrong-token",
            "event": {
                "sender": {"sender_id": {"open_id": "ou_test_user"}},
                "message": {
                    "chat_id": "oc_test_chat",
                    "message_type": "text",
                    "content": json.dumps({"text": "/health"}),
                },
            },
        },
    )

    assert response.status_code == 403
