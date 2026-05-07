from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.enums import JobStatus
from app.db.base import Base
from app.db.models.job import Job
from app.schemas.prompt import PromptItem
from app.schemas.storyboard import StoryboardShotList
from app.services.orchestration_service import OrchestrationService


class FakeOutlineService:
    def generate_outline(self, session, job, model_name):
        return "一个剑客在雨夜追寻仇敌，最终逼近决战。"


class FakeStoryboardService:
    def generate_storyboard(self, session, job, outline_text, model_name):
        return StoryboardShotList.model_validate(
            {
                "shots": [
                    {
                        "shot_index": 1,
                        "scene": "雨夜街巷",
                        "subject": "剑客",
                        "action": "缓步前行",
                        "camera": "中景跟拍",
                        "lighting": "冷色霓虹",
                        "emotion": "压抑",
                        "duration_hint": "3s",
                    }
                ]
            }
        )


class FakePromptService:
    def build_prompts(self, storyboard, style_preset, version):
        return [
            PromptItem(
                shot_index=1,
                positive_prompt="hero in rain",
                negative_prompt="blurry",
                style_tags=[style_preset],
            )
        ]


class FakeImageService:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def generate_assets(self, session, job, prompts, style_preset):
        if self.should_fail:
            raise RuntimeError("image step failed")
        return [{"shot_index": 1, "status": "completed"}]


class FakeQualityService:
    def validate_generation(self, storyboard, prompts, assets):
        class Result:
            result = "passed"
            notes = "ok"
            score = Decimal("1.00")

        return Result()


class FakeNotificationService:
    def __init__(self):
        self.calls = []
        self.asset_calls = []

    def notify_job_event(self, session, job, event_type, message, target_id=None):
        self.calls.append(
            {
                "job_id": job.id,
                "event_type": event_type,
                "message": message,
                "target_id": target_id,
            }
        )

    def notify_asset_image(self, session, job, asset, event_type="job_asset_image", target_id=None):
        self.asset_calls.append(
            {
                "job_id": job.id,
                "asset_status": getattr(asset, "status", None),
                "event_type": event_type,
                "target_id": target_id,
            }
        )


def create_job(session):
    job = Job(
        request_id="req-orchestration",
        topic="冷血剑客复仇",
        style_preset="cinematic",
        target_shot_count=1,
        status=JobStatus.PENDING,
        idempotency_key="orch-key",
        current_step="outline",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def test_orchestration_service_moves_job_to_waiting_review():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    notification_service = FakeNotificationService()
    service = OrchestrationService(
        outline_service=FakeOutlineService(),
        storyboard_service=FakeStoryboardService(),
        prompt_service=FakePromptService(),
        image_service=FakeImageService(),
        quality_service=FakeQualityService(),
        notification_service=notification_service,
    )

    with Session(engine) as session:
        job = create_job(session)

        result = service.run_job(session, job, model_name="gpt-4.1-mini")

        assert result.status == JobStatus.WAITING_REVIEW
        assert result.current_step == "review"
        assert notification_service.calls[-1]["event_type"] == "job_waiting_review"
        assert notification_service.asset_calls[-1]["event_type"] == "job_asset_image"


def test_orchestration_service_marks_job_failed_when_image_step_raises():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    notification_service = FakeNotificationService()
    service = OrchestrationService(
        outline_service=FakeOutlineService(),
        storyboard_service=FakeStoryboardService(),
        prompt_service=FakePromptService(),
        image_service=FakeImageService(should_fail=True),
        quality_service=FakeQualityService(),
        notification_service=notification_service,
    )

    with Session(engine) as session:
        job = create_job(session)

        with pytest.raises(RuntimeError):
            service.run_job(session, job, model_name="gpt-4.1-mini")

        session.refresh(job)
        assert job.status == JobStatus.FAILED
        assert job.current_step == "image"
        assert notification_service.calls[-1]["event_type"] == "job_failed"
