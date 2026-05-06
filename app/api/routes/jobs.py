import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import load_settings
from app.core.enums import JobStatus
from app.db.models.job import Job
from app.db.models.review import Review
from app.db.models.step_run import StepRun
from app.schemas.job import JobCreateRequest
from app.services.factory import build_notification_service
from app.workers.dispatcher import build_job_dispatcher


router = APIRouter(prefix="/jobs", tags=["jobs"])


def get_job_dispatcher():
    return build_job_dispatcher()


def get_notification_service():
    settings = load_settings(allow_placeholder_llm_api_key=True)
    return build_notification_service(settings)


def safe_enqueue(dispatcher, job_id):
    try:
        result = dispatcher.enqueue_job(job_id)
        return {
            "dispatch_status": result["dispatch_status"],
            "queue_name": result["queue_name"],
            "dispatch_error": None,
        }
    except Exception as exc:
        return {
            "dispatch_status": "failed",
            "queue_name": None,
            "dispatch_error": str(exc),
        }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreateRequest,
    db: Session = Depends(get_db),
    dispatcher=Depends(get_job_dispatcher),
    notification_service=Depends(get_notification_service),
):
    job = Job(
        request_id=str(uuid.uuid4()),
        topic=payload.topic,
        style_preset=payload.style_preset,
        target_shot_count=payload.target_shot_count,
        image_backend=payload.image_backend,
        status=JobStatus.PENDING,
        idempotency_key=str(uuid.uuid4()),
        current_step="outline",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    notification_service.notify_job_event(
        db,
        job,
        event_type="job_created",
        message="任务已创建，job_id={0}".format(job.id),
    )
    dispatch_result = safe_enqueue(dispatcher, job.id)
    return {
        "id": job.id,
        "topic": job.topic,
        "status": job.status,
        "current_step": job.current_step,
        "image_backend": job.image_backend,
        "dispatch_status": dispatch_result["dispatch_status"],
        "queue_name": dispatch_result["queue_name"],
        "dispatch_error": dispatch_result["dispatch_error"],
    }


@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "id": job.id,
        "topic": job.topic,
        "status": job.status,
        "current_step": job.current_step,
        "style_preset": job.style_preset,
        "target_shot_count": job.target_shot_count,
        "image_backend": job.image_backend,
    }


@router.get("/{job_id}/steps")
def get_job_steps(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    steps = db.execute(select(StepRun).where(StepRun.job_id == job_id).order_by(StepRun.id)).scalars().all()
    return [
        {
            "id": step.id,
            "step_name": step.step_name,
            "status": step.status,
            "cache_hit": step.cache_hit,
        }
        for step in steps
    ]


@router.post("/{job_id}/retry")
def retry_job(job_id: int, db: Session = Depends(get_db), dispatcher=Depends(get_job_dispatcher)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    job.status = JobStatus.PENDING
    db.commit()
    dispatch_result = safe_enqueue(dispatcher, job.id)
    return {
        "id": job.id,
        "status": job.status,
        "dispatch_status": dispatch_result["dispatch_status"],
        "queue_name": dispatch_result["queue_name"],
        "dispatch_error": dispatch_result["dispatch_error"],
    }


@router.post("/{job_id}/approve")
def approve_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    job.status = JobStatus.COMPLETED
    review = Review(
        job_id=job.id,
        review_type="manual",
        result="approved",
        score=1,
        notes="approved via api",
        reviewed_by="api",
    )
    db.add(review)
    db.commit()
    return {"id": job.id, "status": job.status}


@router.post("/{job_id}/cancel")
def cancel_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    job.status = JobStatus.CANCELLED
    db.commit()
    return {"id": job.id, "status": job.status}
