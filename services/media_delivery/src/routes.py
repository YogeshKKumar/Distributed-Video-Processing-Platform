import glob
import os
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import FileResponse
from shared.config import shared_settings
from shared.storage import StorageManager
try:
    from .streaming import stream_video_file
except (ImportError, ValueError):
    try:
        from src.streaming import stream_video_file
    except (ImportError, ValueError):
        from services.media_delivery.src.streaming import stream_video_file

router = APIRouter(tags=["Media Delivery"])

@router.get("/api/v1/outputs/{video_id}")
def get_available_outputs(video_id: str):
    """
    Returns all available transcoded resolutions, file sizes, and media streaming URLs.
    """
    transcoded_folder = os.path.join(shared_settings.TRANSCODED_DIR, video_id)
    outputs = []

    for res in ["360p", "720p", "1080p"]:
        file_path = os.path.join(transcoded_folder, f"{res}.mp4")
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            outputs.append({
                "video_id": video_id,
                "resolution": res,
                "format": "mp4",
                "file_size": file_size,
                "media_url": f"/media/videos/{video_id}/{res}",
            })

    return outputs


@router.get("/media/videos/{video_id}/{resolution}")
def stream_transcoded_video(video_id: str, resolution: str, request: Request):
    """
    Secure video streaming endpoint with HTTP 206 Range support.
    """
    file_path = StorageManager.get_transcoded_path(video_id, resolution)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcoded video for resolution '{resolution}' not found for video '{video_id}'."
        )
    return stream_video_file(file_path, request, content_type="video/mp4")


@router.get("/media/raw/{video_id}")
def stream_raw_video(video_id: str, request: Request):
    """
    Streams the raw uploaded video.
    """
    upload_folder = os.path.join(shared_settings.UPLOAD_DIR, video_id)
    if not os.path.exists(upload_folder):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video upload directory not found")

    matches = glob.glob(os.path.join(upload_folder, "*"))
    if not matches or not os.path.exists(matches[0]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source video file not found")

    return stream_video_file(matches[0], request, content_type="video/mp4")


@router.get("/media/thumbnails/{thumbnail_id}")
def serve_thumbnail(thumbnail_id: str):
    """
    Serves a thumbnail image by thumbnail_id.
    """
    # Search in all thumbnail video folders
    pattern = os.path.join(shared_settings.THUMBNAILS_DIR, "*", f"{thumbnail_id}.jpg")
    matches = glob.glob(pattern)
    if not matches or not os.path.exists(matches[0]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not found")

    return FileResponse(matches[0], media_type="image/jpeg")


@router.get("/media/thumbnails/video/{video_id}")
def serve_video_primary_thumbnail(video_id: str):
    """
    Serves the primary thumbnail image for a video.
    """
    folder = os.path.join(shared_settings.THUMBNAILS_DIR, video_id)
    if not os.path.exists(folder):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No thumbnails found for this video")

    matches = glob.glob(os.path.join(folder, "*.jpg"))
    if not matches or not os.path.exists(matches[0]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No thumbnail files found")

    return FileResponse(matches[0], media_type="image/jpeg")
