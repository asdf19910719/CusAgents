from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.story_project import StoryProject
from app.db.models.story_shot_video_job import StoryShotVideoJob
from app.db.models.video_job import VideoJob
from app.schemas.story_video import StoryVideoCreateRequest
from app.services.story_video_service import StoryVideoService
from app.workers.dispatcher import build_job_dispatcher


router = APIRouter(prefix="/story-videos", tags=["story-videos"])


def get_story_video_dispatcher():
    return build_job_dispatcher()


def get_story_video_service(dispatcher=Depends(get_story_video_dispatcher)):
    return StoryVideoService(dispatcher=dispatcher)


def project_response(project):
    return {
        "id": project.id,
        "title": project.title,
        "status": project.status,
        "current_stage": project.current_stage,
        "shot_count": len(project.shots),
        "reference_asset_count": len(project.reference_assets),
        "shot_image_count": len(project.shot_images),
    }


def story_video_job_response(story_video_job):
    return {
        "id": story_video_job.id,
        "project_id": story_video_job.project_id,
        "shot_id": story_video_job.shot_id,
        "video_job_id": story_video_job.video_job_id,
        "mode": story_video_job.mode,
        "status": story_video_job.status,
        "submit_id": story_video_job.submit_id,
        "reference_manifest_json": story_video_job.reference_manifest_json,
        "prompt": story_video_job.prompt,
    }


@router.post("/projects", status_code=status.HTTP_201_CREATED)
def create_story_video_project(
    payload: StoryVideoCreateRequest,
    db: Session = Depends(get_db),
    service: StoryVideoService = Depends(get_story_video_service),
):
    project = service.create_project(db, payload)
    return project_response(project)


@router.get("/projects/{project_id}")
def get_story_video_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(StoryProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="story project not found")
    return project_response(project)


@router.post("/projects/{project_id}/videos/next")
def submit_next_story_video(
    project_id: int,
    db: Session = Depends(get_db),
    service: StoryVideoService = Depends(get_story_video_service),
):
    project = db.get(StoryProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="story project not found")
    story_video_job = service.submit_next_shot_video(db, project_id)
    if story_video_job is None:
        return {"project_id": project_id, "status": "completed", "submitted_video_job_id": None}
    return story_video_job_response(story_video_job)


@router.post("/projects/{project_id}/resume")
def resume_story_video_project(
    project_id: int,
    db: Session = Depends(get_db),
    service: StoryVideoService = Depends(get_story_video_service),
):
    project = db.get(StoryProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="story project not found")
    completed_link = (
        db.query(StoryShotVideoJob)
        .join(VideoJob, StoryShotVideoJob.video_job_id == VideoJob.id)
        .filter(StoryShotVideoJob.project_id == project_id)
        .filter(StoryShotVideoJob.status != "completed")
        .filter(VideoJob.status == "completed")
        .order_by(StoryShotVideoJob.id)
        .first()
    )
    if completed_link is None:
        story_video_job = service.submit_next_shot_video(db, project_id)
    else:
        story_video_job = service.mark_shot_video_completed_and_continue(db, completed_link.video_job_id)
    return {
        "project_id": project_id,
        "submitted_video_job_id": getattr(story_video_job, "video_job_id", None),
        "status": "completed" if story_video_job is None else story_video_job.status,
    }
