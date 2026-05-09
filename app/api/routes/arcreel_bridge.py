from pathlib import Path
import uuid
import os
import shutil

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import load_settings
from app.db.models.video_job import VideoJob
from app.api.routes.videos import get_video_dispatcher, refresh_video_job, safe_enqueue_video
from app.schemas.arcreel_bridge import (
    BridgeImageRequest,
    BridgeImageResponse,
    BridgeVideoRequest,
    BridgeVideoResponse,
)
from app.services.factory import build_image_providers


router = APIRouter(prefix="/arcreel/bridge", tags=["arcreel-bridge"])
BRIDGE_OUTPUT_DIR = Path("output/arcreel_bridge/images")


@router.get("/health")
def bridge_health():
    return {
        "image_backends": ["dreamina_cli", "chatgpt_web"],
        "video_backends": ["dreamina_video_cli"],
    }


@router.post("/images", response_model=BridgeImageResponse)
def create_bridge_image(payload: BridgeImageRequest):
    settings = load_settings(allow_placeholder_llm_api_key=True)
    providers = build_image_providers(settings)
    provider = providers.get(payload.backend)
    if provider is None:
        raise HTTPException(status_code=422, detail="invalid image backend")

    result = provider.generate_image(
        1,
        payload.prompt,
        "",
        payload.aspect_ratio,
        0,
    )
    output_name = Path(payload.output_name).name
    if not output_name:
        raise HTTPException(status_code=422, detail="output_name must include a file name")
    output_path = BRIDGE_OUTPUT_DIR / output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(result.image_bytes)
    metadata = getattr(result, "metadata", None) or {}
    return BridgeImageResponse(
        status="succeeded",
        backend=payload.backend,
        file_path=str(output_path),
        submit_id=metadata.get("submit_id") or getattr(result, "remote_job_id", None),
        provider_raw_response=metadata,
    )


def _manifest_from_bridge_images(reference_images):
    return {
        "images": [
            {
                "file_path": item.file_path,
                "file_name": item.file_name or Path(item.file_path).name,
                "role": item.role,
                "usage": item.usage,
                "included": True,
            }
            for item in reference_images
        ],
        "dropped_images": [],
    }


def _mirror_completed_video_for_arcreel(job, file_path):
    source_path = Path(file_path) if file_path else None
    if source_path is None or not source_path.exists():
        return file_path
    host_root = os.environ.get("ARCREEL_PROJECTS_HOST_ROOT")
    if not host_root:
        return file_path
    images = (getattr(job, "reference_manifest_json", None) or {}).get("images") or []
    shot_item = next(
        (item for item in images if item.get("role") == "shot" and str(item.get("file_path", "")).startswith("/app/projects/")),
        None,
    )
    if not shot_item:
        return file_path
    container_path = Path(str(shot_item["file_path"]).replace("\\", "/"))
    parts = container_path.parts
    if len(parts) < 5 or parts[1] != "app" or parts[2] != "projects":
        return file_path
    project_name = parts[3]
    scene_name = container_path.stem
    target_host_path = Path(host_root) / project_name / "videos" / (scene_name + ".mp4")
    target_host_path.parent.mkdir(parents=True, exist_ok=True)
    if source_path.resolve() != target_host_path.resolve():
        shutil.copyfile(source_path, target_host_path)
    return "/app/projects/{0}/videos/{1}.mp4".format(project_name, scene_name)


@router.post("/videos", response_model=BridgeVideoResponse)
def create_bridge_video(
    payload: BridgeVideoRequest,
    db: Session = Depends(get_db),
    dispatcher=Depends(get_video_dispatcher),
):
    job = VideoJob(
        request_id=str(uuid.uuid4()),
        topic=None,
        prompt=payload.prompt,
        backend=payload.backend,
        mode=payload.mode,
        status="pending",
        current_step="submit",
        duration=payload.duration,
        ratio=payload.ratio,
        video_resolution=payload.video_resolution,
        model_version=payload.model_version,
        reference_manifest_json=_manifest_from_bridge_images(payload.reference_images),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    dispatch_result = safe_enqueue_video(dispatcher, job.id)
    return BridgeVideoResponse(
        status=job.status,
        bridge_job_id=job.id,
        backend=job.backend,
        mode=job.mode,
        submit_id=job.submit_id,
        file_path=None,
        provider_raw_response={},
        dispatch_status=dispatch_result["dispatch_status"],
        queue_name=dispatch_result["queue_name"],
        dispatch_error=dispatch_result["dispatch_error"],
    )


@router.post("/videos/{bridge_job_id}/refresh", response_model=BridgeVideoResponse)
def refresh_bridge_video(
    bridge_job_id: int,
    db: Session = Depends(get_db),
    dispatcher=Depends(get_video_dispatcher),
):
    job = db.get(VideoJob, bridge_job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="video job not found")
    if not job.submit_id:
        return BridgeVideoResponse(
            status=job.status,
            bridge_job_id=job.id,
            backend=job.backend,
            mode=job.mode,
            submit_id=None,
            file_path=None,
            provider_raw_response={},
            error_message=job.error_message,
        )
    result = refresh_video_job(bridge_job_id, db=db, notification_service=None, dispatcher=dispatcher)
    query_result = result.get("query_result") or {}
    file_path = None
    if job.assets:
        completed_assets = [asset for asset in job.assets if asset.status == "completed"]
        if completed_assets:
            file_path = completed_assets[-1].file_path
    file_path = _mirror_completed_video_for_arcreel(job, file_path)
    return BridgeVideoResponse(
        status=job.status,
        bridge_job_id=job.id,
        backend=job.backend,
        mode=job.mode,
        submit_id=job.submit_id,
        file_path=file_path,
        provider_raw_response=query_result,
        error_message=job.error_message,
        poll_dispatch_status=result.get("poll_dispatch_status"),
        poll_queue_name=result.get("poll_queue_name"),
        poll_dispatch_error=result.get("poll_dispatch_error"),
    )
