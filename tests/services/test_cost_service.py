from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.job import Job
from app.db.models.step_run import StepRun
from app.services.cost_service import CostService


def test_cost_service_summarizes_job_costs():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = CostService()

    with Session(engine) as session:
        job = Job(
            request_id="req-cost",
            topic="冷血剑客复仇",
            style_preset="cinematic",
            target_shot_count=2,
            status="pending",
            idempotency_key="cost-key",
            current_step="outline",
        )
        session.add(job)
        session.flush()
        session.add_all(
            [
                StepRun(
                    job_id=job.id,
                    step_name="outline",
                    attempt_no=1,
                    status="completed",
                    provider_name="provider",
                    model_name="model",
                    cache_hit=False,
                    input_summary="a",
                    output_summary="b",
                    input_tokens=100,
                    output_tokens=50,
                    cost=Decimal("0.0100"),
                    latency_ms=100,
                ),
                StepRun(
                    job_id=job.id,
                    step_name="storyboard",
                    attempt_no=1,
                    status="completed",
                    provider_name="provider",
                    model_name="model",
                    cache_hit=False,
                    input_summary="a",
                    output_summary="b",
                    input_tokens=200,
                    output_tokens=80,
                    cost=Decimal("0.0200"),
                    latency_ms=120,
                ),
            ]
        )
        session.commit()

        summary = service.summarize_job_cost(session, job.id)
        overall = service.overall_stats(session)

        assert summary["input_tokens"] == 300
        assert summary["output_tokens"] == 130
        assert summary["total_cost"] == "0.0300"
        assert overall["total_jobs"] == 1
