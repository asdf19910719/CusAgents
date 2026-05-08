from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.video_job import VideoJob
from app.schemas.story_video import StoryVideoCreateRequest
from app.services.story_video_service import StoryVideoService


class FakeDispatcher:
    def __init__(self):
        self.calls = []

    def enqueue_video_job(self, video_id):
        self.calls.append(video_id)
        return {"dispatch_status": "enqueued", "queue_name": "video-queue"}


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def make_request():
    return StoryVideoCreateRequest(
        title="雨夜剑客",
        source_text="一个剑客在雨夜寻找真相",
        source_type="outline",
        style_prompt="cinematic noir",
        notification_target_id="chat-story",
        reference_assets=[
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
        shots=[
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
            },
            {
                "shot_index": 2,
                "title": "拔剑",
                "script_text": "主角拔出长剑。",
                "visual_description": "雨水沿剑刃滑落。",
                "camera_motion": "特写切入。",
                "character_names": ["hero"],
                "scene_names": ["alley"],
                "prop_names": [],
                "duration": 5,
                "ratio": "16:9",
            },
        ],
    )


def test_story_video_service_creates_project_with_shots_and_reference_assets():
    session = make_session()
    service = StoryVideoService()

    project = service.create_project(session, make_request())

    assert project.title == "雨夜剑客"
    assert project.status == "draft"
    assert len(project.reference_assets) == 2
    assert len(project.shots) == 2
    assert len(project.shot_images) == 1
    assert project.shots[0].shot_index == 1
    assert project.pipeline_runs[0].checkpoint_json["current_stage"] == "draft"


def test_submit_next_shot_video_creates_video_job_with_multimodal_manifest():
    session = make_session()
    dispatcher = FakeDispatcher()
    service = StoryVideoService(dispatcher=dispatcher)
    project = service.create_project(session, make_request())

    story_video_job = service.submit_next_shot_video(session, project.id)

    assert story_video_job.status == "queued"
    assert story_video_job.mode == "multimodal2video"
    assert dispatcher.calls == [story_video_job.video_job_id]
    assert story_video_job.reference_manifest_json["images"][0]["file_name"] == "shot-001.png"
    assert story_video_job.reference_manifest_json["images"][1]["file_name"] == "hero.png"
    video_job = session.get(VideoJob, story_video_job.video_job_id)
    assert video_job.mode == "multimodal2video"
    assert "shot-001.png：当前分镜图" in video_job.prompt
    assert video_job.reference_manifest_json["images"][0]["file_path"] == "output/shot-001.png"


def test_mark_shot_video_completed_advances_next_pending_shot():
    session = make_session()
    dispatcher = FakeDispatcher()
    service = StoryVideoService(dispatcher=dispatcher)
    project = service.create_project(session, make_request())
    first = service.submit_next_shot_video(session, project.id)
    first_video_job = session.get(VideoJob, first.video_job_id)
    first_video_job.status = "completed"
    session.commit()

    second = service.mark_shot_video_completed_and_continue(session, first.video_job_id)

    assert second.shot.shot_index == 2
    assert second.mode == "multimodal2video"
    assert dispatcher.calls == [first.video_job_id, second.video_job_id]
