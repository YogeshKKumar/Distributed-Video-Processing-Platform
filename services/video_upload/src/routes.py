import uuid
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
try:
    from .db import get_db
    from .models import Video
except (ImportError, ValueError):
    try:
        from src.db import get_db
        from src.models import Video
    except (ImportError, ValueError):
        from services.video_upload.src.db import get_db
        from services.video_upload.src.models import Video
from shared.storage import StorageManager
from shared.messaging import message_broker
from shared.events import VideoUploadedEvent

router = APIRouter(prefix="/api/v1", tags=["Video Upload"])

@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_video(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload request."
        )

    video_id = str(uuid.uuid4())
    video_title = title.strip() if title and title.strip() else file.filename

    # Save and validate file headers / size
    file_path, file_size = StorageManager.save_upload_file(file, video_id)

    # Insert into service-owned database
    video_record = Video(
        id=video_id,
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        content_type=file.content_type or "video/mp4",
        status="UPLOADED",
    )
    db.add(video_record)
    db.commit()
    db.refresh(video_record)

    # Publish video.uploaded event asynchronously
    event = VideoUploadedEvent(
        video_id=video_id,
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        content_type=video_record.content_type,
        title=video_title,
    )
    message_broker.publish_event("video.uploaded", event)

    return {
        "video_id": video_record.id,
        "filename": video_record.filename,
        "title": video_title,
        "file_size": video_record.file_size,
        "content_type": video_record.content_type,
        "status": video_record.status,
        "created_at": video_record.created_at.isoformat() if video_record.created_at else None,
    }


@router.get("/videos")
def list_uploaded_videos(db: Session = Depends(get_db)):
    records = db.query(Video).order_by(Video.created_at.desc()).all()
    return [r.to_dict() for r in records]


@router.get("/videos/{video_id}")
def get_uploaded_video(video_id: str, db: Session = Depends(get_db)):
    record = db.query(Video).filter(Video.id == video_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return record.to_dict()
