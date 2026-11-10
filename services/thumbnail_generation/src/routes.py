from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
try:
    from .db import get_db
    from .models import VideoThumbnail
except (ImportError, ValueError):
    try:
        from src.db import get_db
        from src.models import VideoThumbnail
    except (ImportError, ValueError):
        from services.thumbnail_generation.src.db import get_db
        from services.thumbnail_generation.src.models import VideoThumbnail

router = APIRouter(prefix="/api/v1", tags=["Thumbnails"])

@router.get("/thumbnails/{video_id}")
def get_thumbnails_for_video(video_id: str, db: Session = Depends(get_db)):
    records = db.query(VideoThumbnail).filter(VideoThumbnail.video_id == video_id).all()
    return [r.to_dict() for r in records]

@router.get("/thumbnails/single/{thumbnail_id}")
def get_single_thumbnail(thumbnail_id: str, db: Session = Depends(get_db)):
    record = db.query(VideoThumbnail).filter(VideoThumbnail.id == thumbnail_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not found")
    return record.to_dict()
