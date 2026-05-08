import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.video_asset import VideoAsset
from app.db.models.video_job import VideoJob
from app.services.story_video_service import StoryVideoService
from app.schemas.video import VideoCreateRequest
from app.core.config import load_settings
from app.services.factory import build_dreamina_task_recovery_service
from app.services.factory import build_notification_service
from app.services.video_notification_messages import build_video_completion_message, build_video_failure_message
from app.workers.dispatcher import build_job_dispatcher


router = APIRouter(prefix="/videos", tags=["videos"])


def get_video_dispatcher():
    return build_job_dispatcher()


def get_video_notification_service():
    return build_notification_service(load_settings(allow_placeholder_llm_api_key=True))


def safe_enqueue_video(dispatcher, video_id):
    try:
        result = dispatcher.enqueue_video_job(video_id)
        return {
            "dispatch_status": result["dispatch_status"],
            "queue_name": result["queue_name"],
            "dispatch_error": None,
        }
    except Exception as exc:
        return {"dispatch_status": "failed", "queue_name": None, "dispatch_error": str(exc)}


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


@router.post("", status_code=status.HTTP_201_CREATED)
def create_video_job(payload: VideoCreateRequest, db: Session = Depends(get_db), dispatcher=Depends(get_video_dispatcher)):
    job = VideoJob(
        request_id=str(uuid.uuid4()),
        topic=payload.topic,
        prompt=payload.prompt,
        backend=payload.backend,
        mode=payload.mode,
        status="pending",
        current_step="submit",
        duration=payload.duration,
        ratio=payload.ratio,
        video_resolution=payload.video_resolution,
        model_version=payload.model_version,
        reference_manifest_json=payload.reference_manifest_json,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    dispatch_result = safe_enqueue_video(dispatcher, job.id)
    return {
        "id": job.id,
        "prompt": job.prompt,
        "backend": job.backend,
        "mode": job.mode,
        "status": job.status,
        "current_step": job.current_step,
        "dispatch_status": dispatch_result["dispatch_status"],
        "queue_name": dispatch_result["queue_name"],
        "dispatch_error": dispatch_result["dispatch_error"],
    }


@router.get("/{video_id}")
def get_video_job(video_id: int, db: Session = Depends(get_db)):
    job = db.get(VideoJob, video_id)
    if job is None:
        raise HTTPException(status_code=404, detail="video job not found")
    return {
        "id": job.id,
        "topic": job.topic,
        "prompt": job.prompt,
        "backend": job.backend,
        "mode": job.mode,
        "status": job.status,
        "current_step": job.current_step,
        "duration": job.duration,
        "ratio": job.ratio,
        "video_resolution": job.video_resolution,
        "model_version": job.model_version,
        "submit_id": job.submit_id,
        "reference_manifest_json": job.reference_manifest_json,
        "error_message": job.error_message,
    }


@router.get("/{video_id}/assets")
def list_video_assets(video_id: int, db: Session = Depends(get_db)):
    job = db.get(VideoJob, video_id)
    if job is None:
        raise HTTPException(status_code=404, detail="video job not found")
    assets = db.execute(select(VideoAsset).where(VideoAsset.video_job_id == video_id).order_by(VideoAsset.id)).scalars().all()
    return [
        {
            "id": asset.id,
            "file_path": asset.file_path,
            "status": asset.status,
            "metadata_json": asset.metadata_json,
        }
        for asset in assets
    ]


@router.post("/{video_id}/retry")
def retry_video_job(video_id: int, db: Session = Depends(get_db), dispatcher=Depends(get_video_dispatcher)):
    job = db.get(VideoJob, video_id)
    if job is None:
        raise HTTPException(status_code=404, detail="video job not found")
    job.status = "pending"
    job.current_step = "submit"
    db.commit()
    dispatch_result = safe_enqueue_video(dispatcher, job.id)
    return {
        "id": job.id,
        "status": job.status,
        "dispatch_status": dispatch_result["dispatch_status"],
        "queue_name": dispatch_result["queue_name"],
        "dispatch_error": dispatch_result["dispatch_error"],
    }


@router.post("/{video_id}/cancel")
def cancel_video_job(video_id: int, db: Session = Depends(get_db)):
    job = db.get(VideoJob, video_id)
    if job is None:
        raise HTTPException(status_code=404, detail="video job not found")
    job.status = "cancelled"
    job.current_step = "cancelled"
    db.commit()
    return {"id": job.id, "status": job.status}


@router.post("/{video_id}/refresh")
def refresh_video_job(
    video_id: int,
    db: Session = Depends(get_db),
    notification_service=Depends(get_video_notification_service),
    dispatcher=Depends(get_video_dispatcher),
):
    job = db.get(VideoJob, video_id)
    if job is None:
        raise HTTPException(status_code=404, detail="video job not found")
    if not job.submit_id:
        raise HTTPException(status_code=422, detail="video job has no submit_id")
    service = build_dreamina_task_recovery_service(load_settings(allow_placeholder_llm_api_key=True))
    query_result = service.query_submit_id(job.submit_id)
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
