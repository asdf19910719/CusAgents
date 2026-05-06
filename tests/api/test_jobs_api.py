from fastapi.testclient import TestClient

from app.api.routes.jobs import get_job_dispatcher
from app.main import app


def test_create_and_query_job():
    client = TestClient(app)

    create_response = client.post(
        "/jobs",
        json={
            "topic": "冷血剑客复仇",
            "style_preset": "cinematic",
            "target_shot_count": 3,
            "image_backend": "third_party",
        },
    )

    assert create_response.status_code == 201
    job_id = create_response.json()["id"]

    get_response = client.get("/jobs/{0}".format(job_id))
    steps_response = client.get("/jobs/{0}/steps".format(job_id))

    assert get_response.status_code == 200
    assert get_response.json()["topic"] == "冷血剑客复仇"
    assert get_response.json()["image_backend"] == "third_party"
    assert steps_response.status_code == 200
    assert steps_response.json() == []


def test_create_job_rejects_unknown_image_backend():
    client = TestClient(app)

    create_response = client.post(
        "/jobs",
        json={
            "topic": "冷血剑客复仇",
            "style_preset": "cinematic",
            "target_shot_count": 3,
            "image_backend": "unknown_backend",
        },
    )

    assert create_response.status_code == 422


def test_create_job_enqueues_when_dispatcher_is_overridden():
    class FakeDispatcher:
        def __init__(self):
            self.calls = []

        def enqueue_job(self, job_id):
            self.calls.append(job_id)
            return {"dispatch_status": "enqueued", "queue_name": "test-queue"}

    dispatcher = FakeDispatcher()
    app.dependency_overrides[get_job_dispatcher] = lambda: dispatcher
    client = TestClient(app)

    try:
        create_response = client.post(
            "/jobs",
            json={
                "topic": "冷血剑客复仇",
                "style_preset": "cinematic",
                "target_shot_count": 2,
            },
        )
    finally:
        app.dependency_overrides.pop(get_job_dispatcher, None)

    assert create_response.status_code == 201
    payload = create_response.json()
    assert payload["dispatch_status"] == "enqueued"
    assert payload["queue_name"] == "test-queue"
    assert dispatcher.calls == [payload["id"]]


def test_retry_approve_and_cancel_job():
    client = TestClient(app)
    create_response = client.post(
        "/jobs",
        json={
            "topic": "冷血剑客复仇",
            "style_preset": "cinematic",
            "target_shot_count": 1,
        },
    )
    job_id = create_response.json()["id"]

    retry_response = client.post("/jobs/{0}/retry".format(job_id))
    approve_response = client.post("/jobs/{0}/approve".format(job_id))
    cancel_response = client.post("/jobs/{0}/cancel".format(job_id))

    assert retry_response.status_code == 200
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "completed"
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"


def test_retry_job_reenqueues_when_dispatcher_is_overridden():
    class FakeDispatcher:
        def __init__(self):
            self.calls = []

        def enqueue_job(self, job_id):
            self.calls.append(job_id)
            return {"dispatch_status": "enqueued", "queue_name": "retry-queue"}

    dispatcher = FakeDispatcher()
    app.dependency_overrides[get_job_dispatcher] = lambda: dispatcher
    client = TestClient(app)

    try:
        create_response = client.post(
            "/jobs",
            json={
                "topic": "冷血剑客复仇",
                "style_preset": "cinematic",
                "target_shot_count": 1,
            },
        )
        job_id = create_response.json()["id"]
        retry_response = client.post("/jobs/{0}/retry".format(job_id))
    finally:
        app.dependency_overrides.pop(get_job_dispatcher, None)

    assert retry_response.status_code == 200
    assert retry_response.json()["dispatch_status"] == "enqueued"
    assert retry_response.json()["queue_name"] == "retry-queue"
    assert dispatcher.calls[-1] == job_id


def test_create_job_returns_dispatch_failure_when_dispatcher_raises():
    class FailingDispatcher:
        def enqueue_job(self, job_id):
            raise RuntimeError("redis unavailable")

    app.dependency_overrides[get_job_dispatcher] = lambda: FailingDispatcher()
    client = TestClient(app)

    try:
        create_response = client.post(
            "/jobs",
            json={
                "topic": "冷血剑客复仇",
                "style_preset": "cinematic",
                "target_shot_count": 2,
            },
        )
    finally:
        app.dependency_overrides.pop(get_job_dispatcher, None)

    assert create_response.status_code == 201
    payload = create_response.json()
    assert payload["dispatch_status"] == "failed"
    assert "redis unavailable" in payload["dispatch_error"]


def test_retry_job_returns_dispatch_failure_when_dispatcher_raises():
    class FailingDispatcher:
        def enqueue_job(self, job_id):
            raise RuntimeError("redis unavailable")

    app.dependency_overrides[get_job_dispatcher] = lambda: FailingDispatcher()
    client = TestClient(app)

    try:
        create_response = client.post(
            "/jobs",
            json={
                "topic": "冷血剑客复仇",
                "style_preset": "cinematic",
                "target_shot_count": 1,
            },
        )
        job_id = create_response.json()["id"]
        retry_response = client.post("/jobs/{0}/retry".format(job_id))
    finally:
        app.dependency_overrides.pop(get_job_dispatcher, None)

    assert retry_response.status_code == 200
    assert retry_response.json()["dispatch_status"] == "failed"
    assert "redis unavailable" in retry_response.json()["dispatch_error"]
