import json
import hashlib
import time

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
        def __init__(self):
            self.calls = []

        def notify_job_event(self, session, job, event_type, message, target_id=None):
            self.calls.append(
                {
                    "job_id": getattr(job, "id", None) if job is not None else None,
                    "event_type": event_type,
                    "message": message,
                    "target_id": target_id,
                }
            )
            return None

    notification_service = FakeNotificationService()
    app.dependency_overrides[get_job_dispatcher] = lambda: FakeDispatcher()
    app.dependency_overrides[get_notification_service] = lambda: notification_service
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
    assert notification_service.calls[-1]["event_type"] == "command_result"
    assert notification_service.calls[-1]["target_id"] == "oc_test_chat"


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


def test_feishu_url_verification_bypasses_signature_check(monkeypatch):
    monkeypatch.setenv("FEISHU_ENCRYPT_KEY", "encrypt-key")
    client = TestClient(app)

    response = client.post(
        "/webhooks/feishu/events",
        json={"type": "url_verification", "challenge": "abc123"},
    )

    assert response.status_code == 200
    assert response.json() == {"challenge": "abc123"}


def test_feishu_event_callback_accepts_valid_signature(monkeypatch):
    class FakeNotificationService:
        def notify_job_event(self, session, job, event_type, message, target_id=None):
            return None

    monkeypatch.setenv("FEISHU_ENCRYPT_KEY", "encrypt-key")
    monkeypatch.setenv("FEISHU_WEBHOOK_MAX_AGE_SECONDS", "300")
    app.dependency_overrides[get_notification_service] = lambda: FakeNotificationService()
    client = TestClient(app)
    payload = {
        "type": "event_callback",
        "event": {
            "sender": {"sender_id": {"open_id": "ou_test_user"}},
            "message": {
                "chat_id": "oc_test_chat",
                "message_type": "text",
                "content": json.dumps({"text": "/health"}),
            },
        },
    }
    raw_body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    timestamp = str(int(time.time()))
    nonce = "nonce-1"
    signature = hashlib.sha256(timestamp.encode("utf-8") + nonce.encode("utf-8") + b"encrypt-key" + raw_body).hexdigest()

    try:
        response = client.post(
            "/webhooks/feishu/events",
            content=raw_body,
            headers={
                "content-type": "application/json",
                "x-lark-request-timestamp": timestamp,
                "x-lark-request-nonce": nonce,
                "x-lark-signature": signature,
            },
        )
    finally:
        app.dependency_overrides.pop(get_notification_service, None)

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_feishu_event_callback_rejects_invalid_signature(monkeypatch):
    monkeypatch.setenv("FEISHU_ENCRYPT_KEY", "encrypt-key")
    monkeypatch.setenv("FEISHU_WEBHOOK_MAX_AGE_SECONDS", "300")
    client = TestClient(app)
    payload = {
        "type": "event_callback",
        "event": {
            "sender": {"sender_id": {"open_id": "ou_test_user"}},
            "message": {
                "chat_id": "oc_test_chat",
                "message_type": "text",
                "content": json.dumps({"text": "/health"}),
            },
        },
    }
    raw_body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    response = client.post(
        "/webhooks/feishu/events",
        content=raw_body,
        headers={
            "content-type": "application/json",
            "x-lark-request-timestamp": str(int(time.time())),
            "x-lark-request-nonce": "nonce-1",
            "x-lark-signature": "bad-signature",
        },
    )

    assert response.status_code == 403


def test_feishu_event_callback_rejects_replayed_signature(monkeypatch):
    class FakeNotificationService:
        def notify_job_event(self, session, job, event_type, message, target_id=None):
            return None

    monkeypatch.setenv("FEISHU_ENCRYPT_KEY", "encrypt-key")
    monkeypatch.setenv("FEISHU_WEBHOOK_MAX_AGE_SECONDS", "300")
    app.dependency_overrides[get_notification_service] = lambda: FakeNotificationService()
    client = TestClient(app)
    payload = {
        "type": "event_callback",
        "event": {
            "sender": {"sender_id": {"open_id": "ou_test_user"}},
            "message": {
                "chat_id": "oc_test_chat",
                "message_type": "text",
                "content": json.dumps({"text": "/health"}),
            },
        },
    }
    raw_body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    timestamp = str(int(time.time()))
    nonce = "nonce-replay"
    signature = hashlib.sha256(timestamp.encode("utf-8") + nonce.encode("utf-8") + b"encrypt-key" + raw_body).hexdigest()
    headers = {
        "content-type": "application/json",
        "x-lark-request-timestamp": timestamp,
        "x-lark-request-nonce": nonce,
        "x-lark-signature": signature,
    }

    try:
        first = client.post("/webhooks/feishu/events", content=raw_body, headers=headers)
        second = client.post("/webhooks/feishu/events", content=raw_body, headers=headers)
    finally:
        app.dependency_overrides.pop(get_notification_service, None)

    assert first.status_code == 200
    assert second.status_code == 403
