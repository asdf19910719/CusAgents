from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.video_asset import VideoAsset
from app.db.models.video_job import VideoJob
from app.services.story_video_service import StoryVideoService
from app.services.video_notification_messages import build_video_completion_message, build_video_failure_message


def resolve_video_result_path(query_result):
    for key in ("file_path", "local_path", "download_path", "path", "output_path"):
        value = query_result.get(key)
        if value:
            return Path(str(value).strip().strip('"'))
    return None


def save_refreshed_video_asset(db, job, query_result):
    result_path = resolve_video_result_path(query_result)
    if result_path is None or not result_path.exists():
        return None
    existing_asset = db.execute(
        select(VideoAsset)
        .where(VideoAsset.video_job_id == job.id)
        .where(VideoAsset.metadata_json["submit_id"].as_string() == job.submit_id)
        .where(VideoAsset.status == "completed")
    ).scalars().first()
    if existing_asset is not None:
        return existing_asset
    asset = VideoAsset(
        video_job_id=job.id,
        file_path=str(result_path),
        preview_path=str(result_path),
        thumbnail_path=None,
        duration=job.duration,
        ratio=job.ratio,
        video_resolution=job.video_resolution,
        status="completed",
        metadata_json=query_result,
    )
    db.add(asset)
    return asset


def _notify_video_job(notification_service, db, job, event_type, message):
    if notification_service is not None:
        notification_service.notify_video_job_event(db, job, event_type, message)


def refresh_video_job_status(
    db: Session,
    job: VideoJob,
    recovery_service,
    *,
    download_dir,
    notification_service=None,
    dispatcher=None,
):
    query_result = recovery_service.query_submit_id(job.submit_id, download_dir=download_dir)
    gen_status = query_result.get("gen_status")
    story_next_video_job_id = None
    if gen_status == "success":
        job.status = "completed"
        job.current_step = "completed"
        job.error_message = None
        asset = save_refreshed_video_asset(db, job, query_result)
        _notify_video_job(
            notification_service,
            db,
            job,
            "video_job_completed",
            build_video_completion_message(job, asset=asset, file_path=getattr(asset, "file_path", None), refreshed=True),
        )
        story_next = StoryVideoService(dispatcher=dispatcher).mark_shot_video_completed_and_continue(db, job.id)
        story_next_video_job_id = getattr(story_next, "video_job_id", None)
    elif gen_status == "querying":
        job.status = "querying"
        job.current_step = "query_result"
        job.error_message = None
    elif gen_status == "fail":
        job.status = "failed"
        job.current_step = "failed"
        job.error_message = query_result.get("fail_reason") or "dreamina video generation failed"
        _notify_video_job(
            notification_service,
            db,
            job,
            "video_job_failed",
            build_video_failure_message(job, job.error_message or "dreamina video generation failed", refreshed=True),
        )
    db.commit()
    return {
        "id": job.id,
        "status": job.status,
        "submit_id": job.submit_id,
        "query_result": query_result,
        "story_next_video_job_id": story_next_video_job_id,
    }
