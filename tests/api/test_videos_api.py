from fastapi.testclient import TestClient

from app.api.routes.videos import get_video_dispatcher
from app.main import app


class FakeVideoDispatcher:
    def __init__(self):
        self.calls = []
        self.poll_calls = []

    def enqueue_video_job(self, video_id):
        self.calls.append(video_id)
        return {"dispatch_status": "enqueued", "queue_name": "video-queue"}

    def enqueue_video_poll(self, video_id, delay_seconds):
        self.poll_calls.append({"video_id": video_id, "delay_seconds": delay_seconds})
        return {"dispatch_status": "enqueued", "queue_name": "video-queue"}


def test_create_and_query_video_job():
    dispatcher = FakeVideoDispatcher()
    app.dependency_overrides[get_video_dispatcher] = lambda: dispatcher
    client = TestClient(app)

    try:
        create_response = client.post(
            "/videos",
            json={
                "prompt": "cinematic city sunrise",
                "duration": 4,
                "ratio": "16:9",
                "video_resolution": "720p",
                "model_version": "seedance2.0",
                "backend": "dreamina_video_cli",
            },
        )
        video_id = create_response.json()["id"]
        get_response = client.get("/videos/{0}".format(video_id))
    finally:
        app.dependency_overrides.pop(get_video_dispatcher, None)

    assert create_response.status_code == 201
    assert create_response.json()["backend"] == "dreamina_video_cli"
    assert create_response.json()["dispatch_status"] == "enqueued"
    assert dispatcher.calls == [video_id]
    assert get_response.status_code == 200
    assert get_response.json()["prompt"] == "cinematic city sunrise"


def test_create_video_job_rejects_unknown_backend():
    client = TestClient(app)

    response = client.post(
        "/videos",
        json={
            "prompt": "cinematic city sunrise",
            "duration": 4,
            "backend": "unknown",
        },
    )

    assert response.status_code == 422


def test_create_video_job_accepts_reference_manifest_and_mode():
    dispatcher = FakeVideoDispatcher()
    app.dependency_overrides[get_video_dispatcher] = lambda: dispatcher
    client = TestClient(app)

    try:
        create_response = client.post(
            "/videos",
            json={
                "prompt": "cinematic city sunrise",
                "duration": 4,
                "backend": "dreamina_video_cli",
                "mode": "multimodal2video",
                "reference_manifest_json": {
                    "images": [
                        {"file_path": "output/shot.png", "file_name": "shot.png", "usage": "分镜图"},
                        {"file_path": "output/hero.png", "file_name": "hero.png", "usage": "角色图"},
                    ]
                },
            },
        )
        video_id = create_response.json()["id"]
        get_response = client.get("/videos/{0}".format(video_id))
    finally:
        app.dependency_overrides.pop(get_video_dispatcher, None)

    assert create_response.status_code == 201
    assert get_response.json()["mode"] == "multimodal2video"
    assert get_response.json()["reference_manifest_json"]["images"][1]["file_name"] == "hero.png"


def test_refresh_video_job_queries_saved_submit_id(monkeypatch):
    from app.db.models.video_job import VideoJob
    from app.db.session import SessionLocal

    client = TestClient(app)
    create_response = client.post(
        "/videos",
        json={
            "prompt": "cinematic city sunrise",
            "duration": 4,
            "backend": "dreamina_video_cli",
        },
    )
    video_id = create_response.json()["id"]
    with SessionLocal() as session:
        job = session.get(VideoJob, video_id)
        job.status = "querying"
        job.submit_id = "video-submit-refresh"
        session.commit()

    class FakeRecoveryService:
        def query_submit_id(self, submit_id, download_dir=None):
            assert download_dir is not None
            return {"submit_id": submit_id, "gen_status": "success"}

    monkeypatch.setattr("app.api.routes.videos.build_dreamina_task_recovery_service", lambda settings: FakeRecoveryService())

    response = client.post("/videos/{0}/refresh".format(video_id))

    assert response.status_code == 200
    assert response.json()["submit_id"] == "video-submit-refresh"
    assert response.json()["query_result"]["gen_status"] == "success"


def test_refresh_video_job_saves_asset_when_query_succeeds(monkeypatch, tmp_path):
    from app.db.models.video_asset import VideoAsset
    from app.db.models.video_job import VideoJob
    from app.db.session import SessionLocal

    generated_file = tmp_path / "dreamina-video-refresh.mp4"
    generated_file.write_bytes(b"fake-video-refresh")
    client = TestClient(app)
    create_response = client.post(
        "/videos",
        json={
            "prompt": "cinematic city sunrise",
            "duration": 4,
            "backend": "dreamina_video_cli",
        },
    )
    video_id = create_response.json()["id"]
    with SessionLocal() as session:
        job = session.get(VideoJob, video_id)
        job.status = "querying"
        job.current_step = "query_result"
        job.submit_id = "video-submit-refresh-asset"
        session.commit()

    class FakeRecoveryService:
        def query_submit_id(self, submit_id, download_dir=None):
            assert download_dir == "./output/dreamina/videos"
            return {
                "submit_id": submit_id,
                "gen_status": "success",
                "file_path": str(generated_file),
            }

    monkeypatch.setattr("app.api.routes.videos.build_dreamina_task_recovery_service", lambda settings: FakeRecoveryService())
    notification_calls = []

    class FakeNotificationService:
        def notify_video_job_event(self, session, video_job, event_type, message, target_id=None):
            notification_calls.append(
                {
                    "video_job_id": getattr(video_job, "id", None),
                    "event_type": event_type,
                    "message": message,
                    "target_id": target_id,
                }
            )
            return None

    monkeypatch.setattr("app.api.routes.videos.build_notification_service", lambda settings: FakeNotificationService())

    response = client.post("/videos/{0}/refresh".format(video_id))

    assert response.status_code == 200
    assert notification_calls[0]["event_type"] == "video_job_completed"
    assert "refresh=/videos/{0}/refresh".format(video_id) in notification_calls[0]["message"]
    with SessionLocal() as session:
        assets = session.query(VideoAsset).filter_by(video_job_id=video_id).all()
        assert len(assets) == 1
        assert assets[0].status == "completed"
        assert assets[0].file_path.endswith(".mp4")
        assert assets[0].metadata_json["submit_id"] == "video-submit-refresh-asset"


def test_video_job_can_stay_querying_for_long_running_tasks(monkeypatch):
    from app.db.models.video_job import VideoJob
    from app.db.session import SessionLocal

    client = TestClient(app)
    create_response = client.post(
        "/videos",
        json={
            "prompt": "cinematic city sunrise",
            "duration": 4,
            "backend": "dreamina_video_cli",
        },
    )
    video_id = create_response.json()["id"]
    with SessionLocal() as session:
        job = session.get(VideoJob, video_id)
        job.status = "querying"
        job.submit_id = "video-submit-long"
        job.error_message = "old error"
        session.commit()

    class FakeRecoveryService:
        def query_submit_id(self, submit_id, download_dir=None):
            return {"submit_id": submit_id, "gen_status": "querying"}

    monkeypatch.setattr("app.api.routes.videos.build_dreamina_task_recovery_service", lambda settings: FakeRecoveryService())
    dispatcher = FakeVideoDispatcher()
    app.dependency_overrides[get_video_dispatcher] = lambda: dispatcher

    try:
        response = client.post("/videos/{0}/refresh".format(video_id))
    finally:
        app.dependency_overrides.pop(get_video_dispatcher, None)

    assert response.status_code == 200
    assert response.json()["submit_id"] == "video-submit-long"
    assert response.json()["query_result"]["gen_status"] == "querying"
    assert response.json()["poll_dispatch_status"] == "enqueued"
    assert dispatcher.poll_calls == [{"video_id": video_id, "delay_seconds": 180}]
    with SessionLocal() as session:
        refreshed = session.get(VideoJob, video_id)
        assert refreshed.error_message is None


def test_refresh_video_job_notifies_when_query_fails(monkeypatch):
    from app.db.models.video_job import VideoJob
    from app.db.session import SessionLocal

    client = TestClient(app)
    create_response = client.post(
        "/videos",
        json={
            "prompt": "cinematic city sunrise",
            "duration": 4,
            "backend": "dreamina_video_cli",
        },
    )
    video_id = create_response.json()["id"]
    with SessionLocal() as session:
        job = session.get(VideoJob, video_id)
        job.status = "querying"
        job.submit_id = "video-submit-fail"
        session.commit()

    class FakeRecoveryService:
        def query_submit_id(self, submit_id, download_dir=None):
            return {"submit_id": submit_id, "gen_status": "fail", "fail_reason": "mock fail"}

    notification_calls = []

    class FakeNotificationService:
        def notify_video_job_event(self, session, video_job, event_type, message, target_id=None):
            notification_calls.append({"event_type": event_type, "message": message})
            return None

    monkeypatch.setattr("app.api.routes.videos.build_dreamina_task_recovery_service", lambda settings: FakeRecoveryService())
    monkeypatch.setattr("app.api.routes.videos.build_notification_service", lambda settings: FakeNotificationService())

    response = client.post("/videos/{0}/refresh".format(video_id))

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert notification_calls[0]["event_type"] == "video_job_failed"
    assert "fail_reason=mock fail" in notification_calls[0]["message"]
