from fastapi.testclient import TestClient

from app.api.routes.jobs import get_job_dispatcher, get_notification_service
from app.main import app


class FakeDispatcher:
    def enqueue_job(self, job_id):
        return {"dispatch_status": "enqueued", "queue_name": "mobile-queue"}


class FakeNotificationService:
    def notify_job_event(self, session, job, event_type, message, target_id=None):
        return None


def test_mobile_jobs_page_renders_html():
    client = TestClient(app)

    response = client.get("/mobile/jobs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "移动控制台" in response.text
    assert "创建任务" in response.text


def test_mobile_can_create_job_and_redirect_to_detail():
    app.dependency_overrides[get_job_dispatcher] = lambda: FakeDispatcher()
    app.dependency_overrides[get_notification_service] = lambda: FakeNotificationService()
    client = TestClient(app)

    try:
        response = client.post(
            "/mobile/jobs",
            data={
                "topic": "赛博武侠",
                "style_preset": "cinematic",
                "target_shot_count": "2",
                "image_backend": "third_party",
            },
            follow_redirects=False,
        )
    finally:
        app.dependency_overrides.pop(get_job_dispatcher, None)
        app.dependency_overrides.pop(get_notification_service, None)

    assert response.status_code == 303
    assert response.headers["location"].startswith("/mobile/jobs/")


def test_mobile_job_detail_page_shows_job_state():
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
        detail_response = client.get("/mobile/jobs/{0}".format(job_id))
    finally:
        app.dependency_overrides.pop(get_job_dispatcher, None)
        app.dependency_overrides.pop(get_notification_service, None)

    assert detail_response.status_code == 200
    assert "冷血剑客复仇" in detail_response.text
    assert "pending" in detail_response.text


def test_mobile_job_action_can_approve_and_redirect():
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
        action_response = client.post(
            "/mobile/jobs/{0}/action".format(job_id),
            data={"action": "approve"},
            follow_redirects=False,
        )
        detail_response = client.get("/mobile/jobs/{0}".format(job_id))
    finally:
        app.dependency_overrides.pop(get_job_dispatcher, None)
        app.dependency_overrides.pop(get_notification_service, None)

    assert action_response.status_code == 303
    assert action_response.headers["location"] == "/mobile/jobs/{0}".format(job_id)
    assert "completed" in detail_response.text
