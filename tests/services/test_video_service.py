from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.video_job import VideoJob
from app.providers.image.dreamina_cli_client import DreaminaCliError
from app.providers.video.base import VideoGenerationRequest, VideoGenerationResult
from app.services.video_service import VideoService


class FakeVideoProvider:
    def __init__(self, should_query=False):
        self.should_query = should_query
        self.calls = []

    def generate_video(self, prompt, duration=None, ratio=None, video_resolution=None, model_version=None):
        self.calls.append(
            {
                "prompt": prompt,
                "duration": duration,
                "ratio": ratio,
                "video_resolution": video_resolution,
                "model_version": model_version,
            }
        )
        if self.should_query:
            raise DreaminaCliError(
                "dreamina cli text2video task is still querying; submit_id=video-querying",
                submit_id="video-querying",
                gen_status="querying",
                metadata={
                    "provider_name": "dreamina_video_cli",
                    "submit_id": "video-querying",
                    "gen_status": "querying",
                },
            )
        return VideoGenerationResult(
            provider_name="dreamina_video_cli",
            remote_job_id="video-submit-1",
            video_bytes=b"fake-mp4",
            file_name="dreamina-video",
            file_extension=".mp4",
            metadata={"provider_name": "dreamina_video_cli", "submit_id": "video-submit-1"},
            duration=4,
            ratio="16:9",
            video_resolution="720p",
        )


class FakeNotificationService:
    def __init__(self):
        self.calls = []

    def notify_video_job_event(self, session, video_job, event_type, message, target_id=None):
        self.calls.append(
            {
                "video_job_id": getattr(video_job, "id", None),
                "event_type": event_type,
                "message": message,
                "target_id": target_id,
            }
        )
        return None


def create_video_job(session):
    job = VideoJob(
        request_id="video-request-1",
        topic="city sunrise",
        prompt="cinematic city sunrise",
        backend="dreamina_video_cli",
        mode="text2video",
        status="pending",
        current_step="submit",
        duration=4,
        ratio="16:9",
        video_resolution="720p",
        model_version="seedance2.0",
        notification_target_id="oc_test_chat",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def test_video_service_saves_video_asset_and_completes_job(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = VideoService(provider=FakeVideoProvider(), output_dir=str(tmp_path))

    with Session(engine) as session:
        job = create_video_job(session)
        updated = service.run_video_job(session, job)

        assert updated.status == "completed"
        assert updated.submit_id == "video-submit-1"
        assert len(updated.assets) == 1
        assert updated.assets[0].file_path.endswith(".mp4")
        assert updated.assets[0].metadata_json["submit_id"] == "video-submit-1"
        assert len(service.provider.calls) == 1


def test_video_service_uses_job_generation_parameters(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    provider = FakeVideoProvider()
    service = VideoService(provider=provider, output_dir=str(tmp_path))

    with Session(engine) as session:
        job = create_video_job(session)
        service.run_video_job(session, job)

        assert provider.calls[0]["duration"] == 4
        assert provider.calls[0]["ratio"] == "16:9"
        assert provider.calls[0]["video_resolution"] == "720p"
        assert provider.calls[0]["model_version"] == "seedance2.0"


def test_video_service_marks_querying_and_preserves_submit_id(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = VideoService(provider=FakeVideoProvider(should_query=True), output_dir=str(tmp_path))

    with Session(engine) as session:
        job = create_video_job(session)
        updated = service.run_video_job(session, job)

        assert updated.status == "querying"
        assert updated.submit_id == "video-querying"
        assert "still querying" in updated.error_message


def test_video_service_notifies_when_video_completes(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    notification_service = FakeNotificationService()
    service = VideoService(
        provider=FakeVideoProvider(),
        output_dir=str(tmp_path),
        notification_service=notification_service,
    )

    with Session(engine) as session:
        job = create_video_job(session)
        service.run_video_job(session, job)

        assert notification_service.calls[0]["event_type"] == "video_job_completed"
        assert notification_service.calls[0]["video_job_id"] == job.id
        assert "video_id={0}".format(job.id) in notification_service.calls[0]["message"]
        assert "file_path=" in notification_service.calls[0]["message"]


def test_video_service_notifies_when_video_fails(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    class FailingProvider(FakeVideoProvider):
        def generate_video(self, prompt, duration=None, ratio=None, video_resolution=None, model_version=None):
            raise Exception("boom")

    notification_service = FakeNotificationService()
    service = VideoService(
        provider=FailingProvider(),
        output_dir=str(tmp_path),
        notification_service=notification_service,
    )

    with Session(engine) as session:
        job = create_video_job(session)
        updated = service.run_video_job(session, job)

        assert updated.status == "failed"
        assert notification_service.calls[0]["event_type"] == "video_job_failed"
        assert "fail_reason=" in notification_service.calls[0]["message"]


def test_video_service_passes_reference_manifest_as_structured_request(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    class StructuredProvider:
        def __init__(self):
            self.calls = []

        def generate_video(self, request, duration=None, ratio=None, video_resolution=None, model_version=None):
            self.calls.append(request)
            return VideoGenerationResult(
                provider_name="fake",
                remote_job_id="submit-structured",
                video_bytes=b"fake-video",
                file_name="video",
                file_extension=".mp4",
                metadata={"submit_id": "submit-structured"},
                duration=request.duration,
                ratio=request.ratio,
                video_resolution=request.video_resolution,
            )

    provider = StructuredProvider()
    service = VideoService(provider=provider, output_dir=str(tmp_path))

    with Session(engine) as session:
        job = create_video_job(session)
        job.mode = "multimodal2video"
        job.prompt = "prompt with images"
        job.reference_manifest_json = {
            "images": [
                {"file_path": "output/shot.png", "file_name": "shot.png", "usage": "当前分镜图"},
                {"file_path": "output/hero.png", "file_name": "hero.png", "usage": "主角参考"},
            ]
        }
        session.commit()

        service.run_video_job(session, job)

    assert isinstance(provider.calls[0], VideoGenerationRequest)
    assert provider.calls[0].mode == "multimodal2video"
    assert provider.calls[0].reference_images == ["output/shot.png", "output/hero.png"]
    assert provider.calls[0].reference_image_usages[1]["file_name"] == "hero.png"
