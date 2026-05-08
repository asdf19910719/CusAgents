from app.db.models.video_job import VideoJob
from app.db.session import SessionLocal
from app.core.config import load_settings
from app.services.factory import build_video_service


def execute_video_job(video_id, session_factory, video_service):
    session = session_factory()
    try:
        job = session.get(VideoJob, video_id)
        updated_job = video_service.run_video_job(session, job)
        return {"video_id": updated_job.id, "status": updated_job.status}
    finally:
        session.close()


def run_configured_video_job(video_id):
    settings = load_settings()
    video_service = build_video_service(settings)
    return execute_video_job(video_id, SessionLocal, video_service)
