from fastapi.testclient import TestClient

from app.api.routes.videos import get_video_dispatcher
from app.main import app


class FakeImageResult:
    def __init__(self):
        self.provider_name = "dreamina_cli"
        self.remote_job_id = "remote-image-1"
        self.image_bytes = b"fake-arcreel-image"
        self.file_name = "provider-name"
        self.file_extension = ".png"
        self.metadata = {"submit_id": "img-submit-1", "gen_status": "success"}


class FakeImageProvider:
    def __init__(self):
        self.calls = []

    def generate_image(self, shot_index, positive_prompt, negative_prompt, style_preset, seed):
        self.calls.append(
            {
                "shot_index": shot_index,
                "positive_prompt": positive_prompt,
                "negative_prompt": negative_prompt,
                "style_preset": style_preset,
                "seed": seed,
            }
        )
        return FakeImageResult()


class FakeVideoDispatcher:
    def __init__(self):
        self.calls = []
        self.poll_calls = []

    def enqueue_video_job(self, video_id):
        self.calls.append(video_id)
        return {"dispatch_status": "enqueued", "queue_name": "bridge-video-queue"}

    def enqueue_video_poll(self, video_id, delay_seconds):
        self.poll_calls.append({"video_id": video_id, "delay_seconds": delay_seconds})
        return {"dispatch_status": "enqueued", "queue_name": "bridge-video-queue"}


def test_arcreel_bridge_health_returns_provider_status():
    client = TestClient(app)

    response = client.get("/arcreel/bridge/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["image_backends"] == ["dreamina_cli", "chatgpt_web"]
    assert payload["video_backends"] == ["dreamina_video_cli"]


def test_arcreel_bridge_rejects_unknown_image_backend():
    client = TestClient(app)

    response = client.post(
        "/arcreel/bridge/images",
        json={
            "backend": "unknown",
            "prompt": "test image",
            "output_name": "scene_001.png",
            "aspect_ratio": "16:9",
            "reference_images": [],
        },
    )

    assert response.status_code == 422


def test_arcreel_bridge_image_executes_provider_and_writes_named_file(tmp_path, monkeypatch):
    from app.api.routes import arcreel_bridge

    provider = FakeImageProvider()
    monkeypatch.setattr(arcreel_bridge, "build_image_providers", lambda settings: {"dreamina_cli": provider})
    monkeypatch.setattr(arcreel_bridge, "BRIDGE_OUTPUT_DIR", tmp_path)
    client = TestClient(app)

    response = client.post(
        "/arcreel/bridge/images",
        json={
            "backend": "dreamina_cli",
            "prompt": "cinematic test",
            "output_name": "scene_001.png",
            "aspect_ratio": "16:9",
            "reference_images": [],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["backend"] == "dreamina_cli"
    assert payload["submit_id"] == "img-submit-1"
    assert payload["provider_raw_response"]["gen_status"] == "success"
    assert payload["file_path"].endswith("scene_001.png")
    assert (tmp_path / "scene_001.png").read_bytes() == b"fake-arcreel-image"
    assert provider.calls[0]["positive_prompt"] == "cinematic test"
    assert provider.calls[0]["style_preset"] == "16:9"


def test_arcreel_bridge_video_accepts_multimodal_request_and_persists_manifest():
    dispatcher = FakeVideoDispatcher()
    app.dependency_overrides[get_video_dispatcher] = lambda: dispatcher
    client = TestClient(app)

    try:
        response = client.post(
            "/arcreel/bridge/videos",
            json={
                "backend": "dreamina_video_cli",
                "mode": "multimodal2video",
                "prompt": "use all references",
                "duration": 4,
                "ratio": "16:9",
                "video_resolution": "720p",
                "model_version": "seedance2.0",
                "reference_images": [
                    {
                        "file_path": "output/reference/shot.png",
                        "file_name": "shot.png",
                        "role": "shot",
                        "usage": "shot image",
                    },
                    {
                        "file_path": "output/reference/hero.png",
                        "file_name": "hero.png",
                        "role": "character",
                        "usage": "main character reference",
                    },
                ],
            },
        )
    finally:
        app.dependency_overrides.pop(get_video_dispatcher, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "pending"
    assert payload["bridge_job_id"] is not None
    assert payload["backend"] == "dreamina_video_cli"
    assert payload["mode"] == "multimodal2video"
    assert payload["file_path"] is None
    assert payload["dispatch_status"] == "enqueued"
    assert payload["queue_name"] == "bridge-video-queue"
    assert dispatcher.calls == [payload["bridge_job_id"]]

    detail_response = client.get("/videos/{0}".format(payload["bridge_job_id"]))
    manifest = detail_response.json()["reference_manifest_json"]
    assert manifest["images"][0]["file_name"] == "shot.png"
    assert manifest["images"][0]["included"] is True
    assert manifest["images"][1]["role"] == "character"


def test_arcreel_bridge_video_refresh_maps_video_job_response(monkeypatch):
    from app.api.routes import videos
    from app.db.models.video_job import VideoJob
    from app.db.session import SessionLocal

    class FakeRecoveryService:
        def query_submit_id(self, submit_id, download_dir=None):
            assert submit_id == "bridge-submit-1"
            assert download_dir is not None
            return {
                "gen_status": "querying",
                "submit_id": submit_id,
                "provider_payload": {"status": "still running"},
            }

    monkeypatch.setattr(videos, "build_dreamina_task_recovery_service", lambda settings: FakeRecoveryService())
    dispatcher = FakeVideoDispatcher()
    app.dependency_overrides[get_video_dispatcher] = lambda: dispatcher
    client = TestClient(app)

    try:
        create_response = client.post(
            "/arcreel/bridge/videos",
            json={"prompt": "refresh test", "reference_images": []},
        )
        bridge_job_id = create_response.json()["bridge_job_id"]
        with SessionLocal() as session:
            job = session.get(VideoJob, bridge_job_id)
            job.submit_id = "bridge-submit-1"
            job.status = "querying"
            session.commit()

        response = client.post("/arcreel/bridge/videos/{0}/refresh".format(bridge_job_id))
    finally:
        app.dependency_overrides.pop(get_video_dispatcher, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "querying"
    assert payload["bridge_job_id"] == bridge_job_id
    assert payload["backend"] == "dreamina_video_cli"
    assert payload["mode"] == "text2video"
    assert payload["submit_id"] == "bridge-submit-1"
    assert payload["provider_raw_response"]["gen_status"] == "querying"
    assert payload["poll_dispatch_status"] == "enqueued"
    assert dispatcher.poll_calls == [{"video_id": bridge_job_id, "delay_seconds": 180}]


def test_arcreel_bridge_video_refresh_keeps_pending_job_without_submit_id():
    client = TestClient(app)

    create_response = client.post(
        "/arcreel/bridge/videos",
        json={"prompt": "pending refresh test", "reference_images": []},
    )
    bridge_job_id = create_response.json()["bridge_job_id"]

    response = client.post("/arcreel/bridge/videos/{0}/refresh".format(bridge_job_id))

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "pending"
    assert payload["bridge_job_id"] == bridge_job_id
    assert payload["submit_id"] is None
    assert payload["provider_raw_response"] == {}


def test_arcreel_bridge_video_refresh_returns_completed_file_path(monkeypatch, tmp_path):
    from app.api.routes import videos
    from app.api.routes import arcreel_bridge
    from app.db.models.video_job import VideoJob
    from app.db.session import SessionLocal

    generated_file = tmp_path / "bridge-video.mp4"
    generated_file.write_bytes(b"video")
    projects_root = tmp_path / "projects"

    class FakeRecoveryService:
        def query_submit_id(self, submit_id, download_dir=None):
            return {
                "gen_status": "success",
                "submit_id": submit_id,
                "file_path": str(generated_file),
            }

    monkeypatch.setattr(videos, "build_dreamina_task_recovery_service", lambda settings: FakeRecoveryService())
    monkeypatch.setenv("ARCREEL_PROJECTS_HOST_ROOT", str(projects_root))
    client = TestClient(app)

    create_response = client.post(
        "/arcreel/bridge/videos",
        json={"prompt": "refresh completed test", "reference_images": []},
    )
    bridge_job_id = create_response.json()["bridge_job_id"]
    with SessionLocal() as session:
        job = session.get(VideoJob, bridge_job_id)
        job.submit_id = "bridge-submit-2"
        job.status = "querying"
        job.reference_manifest_json = {
            "images": [
                {
                    "file_path": "/app/projects/demo-project/storyboards/scene_S1.png",
                    "file_name": "scene_S1.png",
                    "role": "shot",
                    "usage": "first frame",
                }
            ]
        }
        session.commit()

    response = client.post("/arcreel/bridge/videos/{0}/refresh".format(bridge_job_id))

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["file_path"] == "/app/projects/demo-project/videos/scene_S1.mp4"
    assert payload["provider_raw_response"]["gen_status"] == "success"
    assert (projects_root / "demo-project" / "videos" / "scene_S1.mp4").read_bytes() == b"video"
