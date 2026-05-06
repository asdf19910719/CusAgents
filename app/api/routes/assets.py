from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.asset import Asset
from app.db.models.job import Job


router = APIRouter(tags=["assets"])


@router.get("/jobs/{job_id}/assets")
def get_job_assets(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    assets = db.execute(select(Asset).where(Asset.job_id == job_id).order_by(Asset.id)).scalars().all()
    return [
        {
            "id": asset.id,
            "shot_index": asset.shot_index,
            "status": asset.status,
            "file_path": asset.file_path,
        }
        for asset in assets
    ]


@router.get("/assets/{asset_id}")
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="asset not found")
    return {
        "id": asset.id,
        "shot_index": asset.shot_index,
        "status": asset.status,
        "file_path": asset.file_path,
        "preview_path": asset.preview_path,
    }
