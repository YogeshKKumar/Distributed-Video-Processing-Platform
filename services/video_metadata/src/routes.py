import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
try:
    from .db import get_db, SessionLocal
    from .models import VideoMetadata
    from .probe import VideoMetadataProbe
except (ImportError, ValueError):
    try:
        from src.db import get_db, SessionLocal
        from src.models import VideoMetadata
        from src.probe import VideoMetadataProbe
    except (ImportError, ValueError):
        from services.video_metadata.src.db import get_db, SessionLocal
        from services.video_metadata.src.models import VideoMetadata
        from services.video_metadata.src.probe import VideoMetadataProbe

logger = logging.getLogger("metadata_routes")
router = APIRouter(prefix="/api/v1", tags=["Video Metadata"])

class MetadataCreateRequest(BaseModel):
    video_id: str
    title: str
    file_path: str
    file_size: int
    format: Optional[str] = "mp4"

class StatusUpdateRequest(BaseModel):
    status: str

@router.get("/videos")
def list_videos(db: Session = Depends(get_db)):
    records = db.query(VideoMetadata).order_by(VideoMetadata.created_at.desc()).all()
    return [r.to_dict() for r in records]

@router.get("/videos/{video_id}")
def get_video_metadata(video_id: str, db: Session = Depends(get_db)):
    record = db.query(VideoMetadata).filter(VideoMetadata.video_id == video_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metadata for video '{video_id}' not found."
        )
    return record.to_dict()

@router.post("/videos", status_code=status.HTTP_201_CREATED)
def create_video_metadata(payload: MetadataCreateRequest, db: Session = Depends(get_db)):
    existing = db.query(VideoMetadata).filter(VideoMetadata.video_id == payload.video_id).first()
    if existing:
        return existing.to_dict()

    probe_data = VideoMetadataProbe.probe_file(payload.file_path)

    metadata = VideoMetadata(
        video_id=payload.video_id,
        title=payload.title,
        format=probe_data.get("format", payload.format),
        duration_seconds=probe_data.get("duration_seconds", 0.0),
        width=probe_data.get("width", 0),
        height=probe_data.get("height", 0),
        bitrate=probe_data.get("bitrate", 0),
        file_size=payload.file_size or probe_data.get("file_size", 0),
        processing_status="PENDING",
    )
    db.add(metadata)
    db.commit()
    db.refresh(metadata)
    return metadata.to_dict()

@router.put("/videos/{video_id}/status")
def update_video_status(video_id: str, payload: StatusUpdateRequest, db: Session = Depends(get_db)):
    record = db.query(VideoMetadata).filter(VideoMetadata.video_id == video_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    record.processing_status = payload.status
    db.commit()
    db.refresh(record)
    return record.to_dict()

def handle_video_uploaded(routing_key: str, body_str: str):
    """
    Consumer callback when video.uploaded event is fired.
    Extracts metadata from source video and stores it.
    """
    import json
    try:
        data = json.loads(body_str)
        video_id = data.get("video_id")
        file_path = data.get("file_path")
        file_size = data.get("file_size", 0)
        title = data.get("title") or data.get("filename")

        if not video_id or not file_path:
            return

        with SessionLocal() as db:
            existing = db.query(VideoMetadata).filter(VideoMetadata.video_id == video_id).first()
            if not existing:
                probe_data = VideoMetadataProbe.probe_file(file_path)
                metadata = VideoMetadata(
                    video_id=video_id,
                    title=title,
                    format=probe_data.get("format", "mp4"),
                    duration_seconds=probe_data.get("duration_seconds", 0.0),
                    width=probe_data.get("width", 0),
                    height=probe_data.get("height", 0),
                    bitrate=probe_data.get("bitrate", 0),
                    file_size=file_size or probe_data.get("file_size", 0),
                    processing_status="PENDING",
                )
                db.add(metadata)
                db.commit()
                logger.info(f"Metadata extracted and stored for video {video_id}")
    except Exception as e:
        logger.error(f"Error handling video.uploaded event: {e}")

def handle_job_status_updated(routing_key: str, body_str: str):
    """
    Consumer callback when job status is updated.
    """
    import json
    try:
        data = json.loads(body_str)
        video_id = data.get("video_id")
        new_status = data.get("status")
        if video_id and new_status:
            with SessionLocal() as db:
                record = db.query(VideoMetadata).filter(VideoMetadata.video_id == video_id).first()
                if record:
                    record.processing_status = new_status
                    db.commit()
                    logger.info(f"Updated status for video {video_id} -> {new_status}")
    except Exception as e:
        logger.error(f"Error updating video status from event: {e}")
