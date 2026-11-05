import os
import json
import uuid
from io import BytesIO
from shared.events import VideoUploadedEvent, TranscodeTaskEvent, ThumbnailTaskEvent
from shared.messaging import message_broker
from services.transcoding_worker.src.worker import process_transcode_task
from services.thumbnail_generation.src.worker import process_thumbnail_task
from services.transcoding_worker.src.ffmpeg_transcoder import FFmpegTranscoder

def test_video_uploaded_triggers_metadata_creation(metadata_client, valid_mp4_bytes):
    video_id = str(uuid.uuid4())
    temp_video_path = os.path.join(metadata_client.app.state._settings.UPLOAD_DIR if hasattr(metadata_client.app.state, "_settings") else "/tmp", f"test_{video_id}.mp4")
    
    # Save a temporary video file
    os.makedirs(os.path.dirname(temp_video_path), exist_ok=True)
    with open(temp_video_path, "wb") as f:
        f.write(valid_mp4_bytes)

    # Publish video.uploaded event
    event = VideoUploadedEvent(
        video_id=video_id,
        filename="intro.mp4",
        file_path=temp_video_path,
        file_size=len(valid_mp4_bytes),
        content_type="video/mp4",
        title="Intro Movie",
    )
    message_broker.publish_event("video.uploaded", event)
    message_broker.in_memory.wait_for_idle()

    # Verify metadata service retrieved and saved metadata
    response = metadata_client.get(f"/api/v1/videos/{video_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == video_id
    assert data["title"] == "Intro Movie"
    assert data["processing_status"] in ("PENDING", "IN_PROGRESS", "COMPLETED")


def test_orchestrator_dispatches_worker_tasks(orchestrator_client, valid_mp4_bytes):
    video_id = str(uuid.uuid4())
    upload_dir = os.path.join(os.environ.get("DATA_DIR", "/tmp"), "uploads", video_id)
    os.makedirs(upload_dir, exist_ok=True)
    raw_path = os.path.join(upload_dir, "raw_video.mp4")
    with open(raw_path, "wb") as f:
        f.write(valid_mp4_bytes)

    # Trigger processing via API
    resp = orchestrator_client.post(f"/api/v1/process/{video_id}")
    assert resp.status_code == 202
    job_data = resp.json()
    assert job_data["video_id"] == video_id
    assert job_data["status"] == "IN_PROGRESS"
    assert "360p" in job_data["target_resolutions"]

    # Verify tasks were dispatched to message broker
    history = message_broker.in_memory._history
    transcode_tasks = [h for h in history if h["routing_key"] == "job.transcode"]
    thumbnail_tasks = [h for h in history if h["routing_key"] == "job.thumbnail"]

    assert len(transcode_tasks) >= 3  # 360p, 720p, 1080p
    assert len(thumbnail_tasks) >= 1


def test_thumbnail_service_generates_and_stores_thumbnail(thumbnail_client, valid_mp4_bytes):
    video_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    upload_dir = os.path.join(os.environ.get("DATA_DIR", "/tmp"), "uploads", video_id)
    os.makedirs(upload_dir, exist_ok=True)
    raw_path = os.path.join(upload_dir, "raw_sample.mp4")
    with open(raw_path, "wb") as f:
        f.write(valid_mp4_bytes)

    thumb_task = ThumbnailTaskEvent(
        job_id=job_id,
        video_id=video_id,
        source_file_path=raw_path,
        time_offset_seconds=1.0,
    )
    # Execute thumbnail worker task
    process_thumbnail_task("job.thumbnail", thumb_task.to_json())

    # Verify thumbnail record exists via API
    resp = thumbnail_client.get(f"/api/v1/thumbnails/{video_id}")
    assert resp.status_code == 200
    thumbs = resp.json()
    assert len(thumbs) >= 1
    assert thumbs[0]["status"] == "COMPLETED"
    assert thumbs[0]["video_id"] == video_id
