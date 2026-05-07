from pathlib import Path

from fastapi.testclient import TestClient
from app.api.routes.jobs import get_job_dispatcher, get_notification_service
from app.db.models.asset import Asset
from app.db.session import SessionLocal
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


def test_mobile_can_create_codex_cli_job_and_redirect_to_detail():
    app.dependency_overrides[get_job_dispatcher] = lambda: FakeDispatcher()
    app.dependency_overrides[get_notification_service] = lambda: FakeNotificationService()
    client = TestClient(app)

    try:
        response = client.post(
            "/mobile/jobs",
            data={
                "topic": "璧涘崥姝︿緺",
                "style_preset": "cinematic",
                "target_shot_count": "2",
                "image_backend": "codex_cli",
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


def test_mobile_jobs_page_redirects_to_login_when_access_token_is_configured(monkeypatch):
    monkeypatch.setenv("MOBILE_ACCESS_TOKEN", "secret-token")
    client = TestClient(app)

    response = client.get("/mobile/jobs", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/mobile/login"


def test_mobile_login_sets_session_and_allows_access(monkeypatch):
    monkeypatch.setenv("MOBILE_ACCESS_TOKEN", "secret-token")
    client = TestClient(app)

    login_page = client.get("/mobile/login")
    login_response = client.post(
        "/mobile/login",
        data={"access_token": "secret-token"},
        follow_redirects=False,
    )
    jobs_page = client.get("/mobile/jobs")

    assert login_page.status_code == 200
    assert "登录" in login_page.text
    assert login_response.status_code == 303
    assert login_response.headers["location"] == "/mobile/jobs"
    assert jobs_page.status_code == 200
    assert "移动控制台" in jobs_page.text


def test_mobile_login_rejects_invalid_token(monkeypatch):
    monkeypatch.setenv("MOBILE_ACCESS_TOKEN", "secret-token")
    client = TestClient(app)

    response = client.post("/mobile/login", data={"access_token": "bad-token"})

    assert response.status_code == 403


def test_mobile_logout_clears_session(monkeypatch):
    monkeypatch.setenv("MOBILE_ACCESS_TOKEN", "secret-token")
    client = TestClient(app)

    client.post("/mobile/login", data={"access_token": "secret-token"}, follow_redirects=False)
    logout_response = client.post("/mobile/logout", follow_redirects=False)
    jobs_response = client.get("/mobile/jobs", follow_redirects=False)

    assert logout_response.status_code == 303
    assert logout_response.headers["location"] == "/mobile/login"
    assert jobs_response.status_code == 303
    assert jobs_response.headers["location"] == "/mobile/login"


def test_mobile_job_detail_shows_asset_preview_link_and_preview_route_serves_image(tmp_path):
    app.dependency_overrides[get_job_dispatcher] = lambda: FakeDispatcher()
    app.dependency_overrides[get_notification_service] = lambda: FakeNotificationService()
    client = TestClient(app)

    try:
        create_response = client.post(
            "/jobs",
            json={
                "topic": "鍐疯鍓戝澶嶄粐",
                "style_preset": "cinematic",
                "target_shot_count": 1,
                "image_backend": "third_party",
            },
        )
        job_id = create_response.json()["id"]
        image_path = tmp_path / "preview.png"
        image_path.write_bytes(b"\x89PNG\r\n\x1a\nfake")

        with SessionLocal() as session:
            session.add(
                Asset(
                    job_id=job_id,
                    shot_index=1,
                    prompt_text="hero in rain",
                    negative_prompt="blurry",
                    seed=1001,
                    workflow_json={"provider_name": "third_party"},
                    file_path=str(image_path),
                    preview_path=str(image_path),
                    status="completed",
                )
            )
            session.commit()
            asset_id = session.query(Asset).order_by(Asset.id.desc()).first().id

        detail_response = client.get("/mobile/jobs/{0}".format(job_id))
        preview_response = client.get("/mobile/assets/{0}/preview".format(asset_id))
    finally:
        app.dependency_overrides.pop(get_job_dispatcher, None)
        app.dependency_overrides.pop(get_notification_service, None)

    assert detail_response.status_code == 200
    assert "/mobile/assets/{0}/preview".format(asset_id) in detail_response.text
    assert preview_response.status_code == 200
    assert preview_response.headers["content-type"].startswith("image/png")
