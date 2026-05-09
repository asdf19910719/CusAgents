from app.db.models.video_job import VideoJob
from app.db.session import SessionLocal
from app.core.config import load_settings
from app.services.factory import build_dreamina_task_recovery_service, build_notification_service, build_video_service
from app.services.video_refresh_service import refresh_video_job_status
from app.workers.dispatcher import build_job_dispatcher


def execute_video_job(video_id, session_factory, video_service):
    session = session_factory()
    try:
        job = session.get(VideoJob, video_id)
        updated_job = video_service.run_video_job(session, job)
        return {"video_id": updated_job.id, "status": updated_job.status}
    finally:
        session.close()


def poll_video_job(
    video_id,
    session_factory,
    recovery_service,
    dispatcher,
    download_dir,
    poll_delay_seconds,
    notification_service=None,
):
    session = session_factory()
    try:
        job = session.get(VideoJob, video_id)
        if job is None:
            return {"video_id": video_id, "status": "missing", "poll_dispatch_status": None}
        if not job.submit_id:
            return {"video_id": video_id, "status": job.status, "poll_dispatch_status": None}
        result = refresh_video_job_status(
            session,
            job,
            recovery_service,
            download_dir=download_dir,
            notification_service=notification_service,
            dispatcher=dispatcher,
        )
        poll_dispatch_status = None
        if result["status"] == "querying":
            dispatch_result = dispatcher.enqueue_video_poll(video_id, delay_seconds=poll_delay_seconds)
            poll_dispatch_status = dispatch_result["dispatch_status"]
        result["poll_dispatch_status"] = poll_dispatch_status
        return result
    finally:
        session.close()


def run_configured_video_job(video_id):
    settings = load_settings()
    video_service = build_video_service(settings)
    result = execute_video_job(video_id, SessionLocal, video_service)
    if result["status"] == "querying":
        dispatcher = build_job_dispatcher(settings)
        dispatcher.enqueue_video_poll(video_id, delay_seconds=settings.dreamina_video_poll_seconds)
    return result


def poll_configured_video_job(video_id):
    settings = load_settings()
    return poll_video_job(
        video_id,
        session_factory=SessionLocal,
        recovery_service=build_dreamina_task_recovery_service(settings),
        dispatcher=build_job_dispatcher(settings),
        download_dir=settings.dreamina_video_output_dir,
        poll_delay_seconds=settings.dreamina_video_poll_seconds,
        notification_service=build_notification_service(settings),
    )
