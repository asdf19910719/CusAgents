from fastapi.testclient import TestClient

from app.api.routes.story_videos import get_story_video_dispatcher
from app.api.routes.videos import get_video_dispatcher
from app.main import app


class FakeStoryVideoDispatcher:
    def __init__(self):
        self.calls = []

    def enqueue_video_job(self, video_id):
        self.calls.append(video_id)
        return {"dispatch_status": "enqueued", "queue_name": "video-queue"}


def story_project_payload():
    return {
        "title": "雨夜剑客",
        "source_text": "一个剑客在雨夜寻找真相",
        "source_type": "outline",
        "style_prompt": "cinematic noir",
        "reference_assets": [
            {
                "asset_type": "character_turnaround",
                "name": "hero",
                "description": "黑衣剑客三视图",
                "prompt": "hero turnaround",
                "file_path": "output/hero.png",
            },
            {
                "asset_type": "scene",
                "name": "alley",
                "description": "雨夜小巷",
                "prompt": "rain alley",
                "file_path": "output/alley.png",
            },
        ],
        "shots": [
            {
                "shot_index": 1,
                "title": "雨夜回头",
                "script_text": "主角在雨夜小巷中回头。",
                "visual_description": "霓虹灯反射在积水上。",
                "camera_motion": "低角度缓慢推近。",
                "character_names": ["hero"],
                "scene_names": ["alley"],
                "prop_names": [],
                "duration": 5,
                "ratio": "16:9",
                "shot_image_path": "output/shot-001.png",
            }
        ],
    }


def test_create_and_get_story_video_project():
    client = TestClient(app)

    create_response = client.post("/story-videos/projects", json=story_project_payload())
    project_id = create_response.json()["id"]
    get_response = client.get("/story-videos/projects/{0}".format(project_id))

    assert create_response.status_code == 201
    assert create_response.json()["title"] == "雨夜剑客"
    assert create_response.json()["shot_count"] == 1
    assert get_response.status_code == 200
    assert get_response.json()["reference_asset_count"] == 2


def test_submit_next_story_shot_video():
    dispatcher = FakeStoryVideoDispatcher()
    app.dependency_overrides[get_story_video_dispatcher] = lambda: dispatcher
    app.dependency_overrides[get_video_dispatcher] = lambda: dispatcher
    client = TestClient(app)

    try:
        create_response = client.post("/story-videos/projects", json=story_project_payload())
        project_id = create_response.json()["id"]
        submit_response = client.post("/story-videos/projects/{0}/videos/next".format(project_id))
    finally:
        app.dependency_overrides.pop(get_story_video_dispatcher, None)
        app.dependency_overrides.pop(get_video_dispatcher, None)

    assert submit_response.status_code == 200
    assert submit_response.json()["mode"] == "multimodal2video"
    assert dispatcher.calls == [submit_response.json()["video_job_id"]]
    assert submit_response.json()["reference_manifest_json"]["images"][0]["file_name"] == "shot-001.png"


def test_resume_story_project_advances_after_completed_video_job():
    dispatcher = FakeStoryVideoDispatcher()
    app.dependency_overrides[get_story_video_dispatcher] = lambda: dispatcher
    client = TestClient(app)

    try:
        payload = story_project_payload()
        payload["shots"].append(
            {
                "shot_index": 2,
                "title": "拔剑",
                "script_text": "主角拔剑。",
                "visual_description": "雨水沿剑刃滑落。",
                "camera_motion": "特写切入。",
                "character_names": ["hero"],
                "scene_names": ["alley"],
                "prop_names": [],
                "duration": 5,
                "ratio": "16:9",
            }
        )
        create_response = client.post("/story-videos/projects", json=payload)
        project_id = create_response.json()["id"]
        first_response = client.post("/story-videos/projects/{0}/videos/next".format(project_id))
        first_video_id = first_response.json()["video_job_id"]

        from app.db.models.video_job import VideoJob
        from app.db.session import SessionLocal

        with SessionLocal() as session:
            job = session.get(VideoJob, first_video_id)
            job.status = "completed"
            session.commit()

        resume_response = client.post("/story-videos/projects/{0}/resume".format(project_id))
    finally:
        app.dependency_overrides.pop(get_story_video_dispatcher, None)

    assert resume_response.status_code == 200
    assert resume_response.json()["submitted_video_job_id"] != first_video_id
    assert dispatcher.calls == [first_video_id, resume_response.json()["submitted_video_job_id"]]


def test_video_refresh_success_advances_story_project(monkeypatch, tmp_path):
    dispatcher = FakeStoryVideoDispatcher()
    app.dependency_overrides[get_story_video_dispatcher] = lambda: dispatcher
    app.dependency_overrides[get_video_dispatcher] = lambda: dispatcher
    client = TestClient(app)
    generated_file = tmp_path / "story-refresh.mp4"
    generated_file.write_bytes(b"fake-video")

    class FakeRecoveryService:
        def query_submit_id(self, submit_id, download_dir=None):
            return {
                "submit_id": submit_id,
                "gen_status": "success",
                "file_path": str(generated_file),
            }

    monkeypatch.setattr("app.api.routes.videos.build_dreamina_task_recovery_service", lambda settings: FakeRecoveryService())

    try:
        payload = story_project_payload()
        payload["shots"].append(
            {
                "shot_index": 2,
                "title": "拔剑",
                "script_text": "主角拔剑。",
                "visual_description": "雨水沿剑刃滑落。",
                "camera_motion": "特写切入。",
                "character_names": ["hero"],
                "scene_names": ["alley"],
                "prop_names": [],
                "duration": 5,
                "ratio": "16:9",
            }
        )
        create_response = client.post("/story-videos/projects", json=payload)
        project_id = create_response.json()["id"]
        first_response = client.post("/story-videos/projects/{0}/videos/next".format(project_id))
        first_video_id = first_response.json()["video_job_id"]

        from app.db.models.video_job import VideoJob
        from app.db.session import SessionLocal

        with SessionLocal() as session:
            job = session.get(VideoJob, first_video_id)
            job.status = "querying"
            job.submit_id = "story-refresh-submit"
            session.commit()

        refresh_response = client.post("/videos/{0}/refresh".format(first_video_id))
    finally:
        app.dependency_overrides.pop(get_story_video_dispatcher, None)
        app.dependency_overrides.pop(get_video_dispatcher, None)

    assert refresh_response.status_code == 200
    assert refresh_response.json()["story_next_video_job_id"] is not None
    assert refresh_response.json()["story_next_video_job_id"] != first_video_id
    assert dispatcher.calls == [first_video_id, refresh_response.json()["story_next_video_job_id"]]
