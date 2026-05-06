from app.db.models.job import Job
from app.db.session import SessionLocal
from app.core.config import load_settings
from app.services.factory import build_orchestration_service


def execute_job(job_id, session_factory, orchestration_service, model_name):
    session = session_factory()
    try:
        job = session.get(Job, job_id)
        updated_job = orchestration_service.run_job(session, job, model_name=model_name)
        return {"job_id": updated_job.id, "status": updated_job.status}
    finally:
        session.close()


def run_default_job(job_id, orchestration_service, model_name):
    return execute_job(
        job_id=job_id,
        session_factory=SessionLocal,
        orchestration_service=orchestration_service,
        model_name=model_name,
    )


def run_configured_job(job_id):
    settings = load_settings()
    orchestration_service = build_orchestration_service(settings)
    return execute_job(
        job_id=job_id,
        session_factory=SessionLocal,
        orchestration_service=orchestration_service,
        model_name=settings.llm_default_model,
    )
