from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from services.transcoding_orchestrator.src.db import get_db
from services.transcoding_orchestrator.src.models import ProcessingJob
from services.transcoding_orchestrator.src.orchestrator import TranscodingOrchestrator

router = APIRouter(prefix="/api/v1", tags=["Transcoding Orchestrator"])

class ProcessRequest(BaseModel):
    resolutions: Optional[List[str]] = None

@router.post("/process/{video_id}", status_code=status.HTTP_202_ACCEPTED)
def trigger_processing(
    video_id: str,
    payload: Optional[ProcessRequest] = None,
    db: Session = Depends(get_db),
):
    try:
        resolutions = payload.resolutions if payload else None
        job = TranscodingOrchestrator.start_processing(video_id, db, resolutions)
        return job.to_dict()
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate transcoding job: {str(e)}"
        )

@router.get("/status/{video_id}")
def get_video_processing_status(video_id: str, db: Session = Depends(get_db)):
    job = db.query(ProcessingJob).filter(ProcessingJob.video_id == video_id).order_by(ProcessingJob.created_at.desc()).first()
    if not job:
        return {
            "video_id": video_id,
            "status": "UNPROCESSED",
            "progress_percent": 0,
            "target_resolutions": [],
            "completed_resolutions": [],
            "thumbnail_status": "NONE",
            "retry_count": 0,
            "error_message": None,
        }
    return job.to_dict()

@router.get("/jobs/{job_id}")
def get_job_by_id(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found")
    return job.to_dict()

@router.get("/jobs")
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(ProcessingJob).order_by(ProcessingJob.created_at.desc()).limit(50).all()
    return [j.to_dict() for j in jobs]
