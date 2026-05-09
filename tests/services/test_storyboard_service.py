from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.job import Job
from app.db.models.llm_cache import LlmCache
from app.db.models.step_run import StepRun
from app.providers.llm.base import StructuredGenerationResult
from app.schemas.storyboard import StoryboardShotList
from app.services.cache_service import CacheService
from app.services.prompt_service import PromptTemplateService
from app.services.storyboard_service import StoryboardService


class FakeStoryboardProvider:
    def __init__(self, parsed):
        self.calls = 0
        self.parsed = parsed

    def generate_structured(self, prompt, schema, model=None):
        self.calls += 1
        return StructuredGenerationResult(
            parsed=schema.model_validate(self.parsed),
            content=str(self.parsed),
            input_tokens=100,
            output_tokens=140,
            total_tokens=240,
            cost=Decimal("0.0200"),
            raw_response={"prompt": prompt},
        )


def create_job(session):
    job = Job(
        request_id="req-storyboard",
        topic="冷血剑客复仇",
        style_preset="cinematic",
        target_shot_count=2,
        status="pending",
        idempotency_key="storyboard-key",
        current_step="storyboard",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def valid_storyboard_payload():
    return {
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
            },
            {
                "shot_index": 2,
                "scene": "屋檐下",
                "subject": "仇人",
                "action": "抬头冷笑",
                "camera": "特写",
                "lighting": "侧逆光",
                "emotion": "挑衅",
                "duration_hint": "2s",
            },
        ]
    }


def test_storyboard_service_generates_valid_storyboard():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    provider = FakeStoryboardProvider(valid_storyboard_payload())
    prompt_service = PromptTemplateService(template_root="app/templates")
    cache_service = CacheService()
    service = StoryboardService(provider, prompt_service, cache_service)

    with Session(engine) as session:
        job = create_job(session)

        result = service.generate_storyboard(
            session,
            job,
            outline_text="一个剑客在雨夜追寻仇敌，最终逼近决战。",
            model_name="gpt-4.1-mini",
        )

        step_run = session.execute(select(StepRun).where(StepRun.job_id == job.id)).scalar_one()
        assert isinstance(result, StoryboardShotList)
        assert len(result.shots) == 2
        assert step_run.status == "completed"
        cache = session.execute(select(LlmCache).where(LlmCache.step_name == "storyboard")).scalar_one()
        assert cache.prompt_version == "v2"


def test_storyboard_service_records_failure_summary_on_invalid_output():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    bad_payload = valid_storyboard_payload()
    bad_payload["shots"][1]["shot_index"] = 3
    provider = FakeStoryboardProvider(bad_payload)
    prompt_service = PromptTemplateService(template_root="app/templates")
    cache_service = CacheService()
    service = StoryboardService(provider, prompt_service, cache_service)

    with Session(engine) as session:
        job = create_job(session)

        with pytest.raises(Exception):
            service.generate_storyboard(
                session,
                job,
                outline_text="一个剑客在雨夜追寻仇敌，最终逼近决战。",
                model_name="gpt-4.1-mini",
            )

        step_run = session.execute(select(StepRun).where(StepRun.job_id == job.id)).scalar_one()
        assert step_run.status == "failed"
        assert "sequential" in step_run.error_message
