import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.video_job import VideoJob
from app.schemas.video import VideoCreateRequest
from app.core.config import load_settings
from app.services.factory import build_dreamina_task_recovery_service
from app.services.factory import build_notification_service
from app.services.video_refresh_service import refresh_video_job_status
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
    settings = load_settings(allow_placeholder_llm_api_key=True)
    service = build_dreamina_task_recovery_service(settings)
    result = refresh_video_job_status(
        db,
        job,
        service,
        download_dir=settings.dreamina_video_output_dir,
        notification_service=notification_service,
        dispatcher=dispatcher,
    )
    result["poll_dispatch_status"] = None
    result["poll_queue_name"] = None
    result["poll_dispatch_error"] = None
    if result["status"] == "querying":
        try:
            dispatch_result = dispatcher.enqueue_video_poll(job.id, delay_seconds=settings.dreamina_video_poll_seconds)
            result["poll_dispatch_status"] = dispatch_result["dispatch_status"]
            result["poll_queue_name"] = dispatch_result["queue_name"]
        except Exception as exc:
            result["poll_dispatch_status"] = "failed"
            result["poll_dispatch_error"] = str(exc)
    return result
