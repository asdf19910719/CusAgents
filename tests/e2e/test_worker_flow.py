from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.core.enums import JobStatus
from app.db.base import Base
from app.db.models.job import Job
from app.workers import jobs as worker_jobs
from app.workers.jobs import execute_job


class FakeOrchestrationService:
    def run_job(self, session, job, model_name):
        job.status = JobStatus.WAITING_REVIEW
        job.current_step = "review"
        session.commit()
        session.refresh(job)
        return job


def test_execute_job_processes_job_with_session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with Session(engine) as session:
        job = Job(
            request_id="req-worker",
            topic="冷血剑客复仇",
            style_preset="cinematic",
            target_shot_count=1,
            status=JobStatus.PENDING,
            idempotency_key="worker-key",
            current_step="outline",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

    result = execute_job(
        job_id=job_id,
        session_factory=session_factory,
        orchestration_service=FakeOrchestrationService(),
        model_name="gpt-4.1-mini",
    )

    assert result["job_id"] == job_id
    assert result["status"] == JobStatus.WAITING_REVIEW


def test_run_configured_job_uses_built_orchestration_service(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with Session(engine) as session:
        job = Job(
            request_id="req-worker-configured",
            topic="冷血剑客复仇",
            style_preset="cinematic",
            target_shot_count=1,
            status=JobStatus.PENDING,
            idempotency_key="worker-configured-key",
            current_step="outline",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

    class FakeOrchestrationService:
        def run_job(self, session, job, model_name):
            job.status = JobStatus.WAITING_REVIEW
            job.current_step = "review"
            session.commit()
            session.refresh(job)
            return job

    monkeypatch.setattr(worker_jobs, "SessionLocal", session_factory)
    monkeypatch.setattr(worker_jobs, "build_orchestration_service", lambda settings: FakeOrchestrationService())

    result = worker_jobs.run_configured_job(job_id)

    assert result["job_id"] == job_id
    assert result["status"] == JobStatus.WAITING_REVIEW


def test_run_configured_job_loads_runtime_settings(monkeypatch):
    captured = {}

    class FakeOrchestrationService:
        def run_job(self, session, job, model_name):
            captured["model_name"] = model_name
            return job

    def fake_load_settings():
        return Settings(
            LLM_API_KEY="real-worker-key",
            LLM_DEFAULT_MODEL="worker-real-model",
        )

    def fake_build_orchestration_service(settings):
        captured["settings"] = settings
        return FakeOrchestrationService()

    monkeypatch.setattr(worker_jobs, "load_settings", fake_load_settings)
    monkeypatch.setattr(worker_jobs, "build_orchestration_service", fake_build_orchestration_service)
    monkeypatch.setattr(
        worker_jobs,
        "execute_job",
        lambda job_id, session_factory, orchestration_service, model_name: {
            "job_id": job_id,
            "status": "stubbed",
            "model_name": model_name,
        },
    )

    result = worker_jobs.run_configured_job("job-123")

    assert result["job_id"] == "job-123"
    assert result["model_name"] == "worker-real-model"
    assert captured["settings"].llm_api_key == "real-worker-key"
