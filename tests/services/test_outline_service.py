from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.job import Job
from app.db.models.step_run import StepRun
from app.providers.llm.base import TextGenerationResult
from app.services.cache_service import CacheService
from app.services.outline_service import OutlineService
from app.services.prompt_service import PromptTemplateService


class FakeOutlineProvider:
    def __init__(self):
        self.calls = 0

    def generate_text(self, prompt, model=None):
        self.calls += 1
        return TextGenerationResult(
            content="一个剑客在雨夜追寻仇敌，最终逼近决战。",
            input_tokens=120,
            output_tokens=80,
            total_tokens=200,
            cost=Decimal("0.0123"),
            raw_response={"prompt": prompt},
        )


def create_job(session):
    job = Job(
        request_id="req-outline",
        topic="冷血剑客复仇",
        style_preset="cinematic",
        target_shot_count=8,
        status="pending",
        idempotency_key="outline-key",
        current_step="outline",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def test_outline_service_generates_outline_and_records_step_run():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    provider = FakeOutlineProvider()
    prompt_service = PromptTemplateService(template_root="app/templates")
    cache_service = CacheService()
    service = OutlineService(provider, prompt_service, cache_service)

    with Session(engine) as session:
        job = create_job(session)

        outline = service.generate_outline(session, job, model_name="gpt-4.1-mini")

        step_run = session.execute(select(StepRun).where(StepRun.job_id == job.id)).scalar_one()
        assert "剑客" in outline
        assert step_run.step_name == "outline"
        assert step_run.cache_hit is False
        assert provider.calls == 1


def test_outline_service_uses_cache_before_calling_provider():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    provider = FakeOutlineProvider()
    prompt_service = PromptTemplateService(template_root="app/templates")
    cache_service = CacheService()
    service = OutlineService(provider, prompt_service, cache_service)

    with Session(engine) as session:
        job = create_job(session)

        first_outline = service.generate_outline(session, job, model_name="gpt-4.1-mini")
        second_outline = service.generate_outline(session, job, model_name="gpt-4.1-mini")

        assert first_outline == second_outline
        assert provider.calls == 1
