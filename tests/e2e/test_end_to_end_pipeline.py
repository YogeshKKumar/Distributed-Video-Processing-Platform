import os
import uuid
from io import BytesIO
from shared.events import VideoUploadedEvent
from shared.messaging import message_broker
from services.transcoding_orchestrator.src.orchestrator import TranscodingOrchestrator
from services.transcoding_orchestrator.src.db import SessionLocal as OrchSessionLocal
from services.transcoding_worker.src.worker import process_transcode_task
from services.thumbnail_generation.src.worker import process_thumbnail_task

def test_full_end_to_end_pipeline(
    upload_client,
    metadata_client,
    orchestrator_client,
    media_client,
    thumbnail_client,
    valid_mp4_bytes,
):
    # 1. User uploads a video
    file_payload = {"file": ("nature_walk.mp4", BytesIO(valid_mp4_bytes), "video/mp4")}
    data = {"title": "Nature Walk 4K"}
    upload_res = upload_client.post("/api/v1/upload", files=file_payload, data=data)
    assert upload_res.status_code == 201
    upload_json = upload_res.json()
    video_id = upload_json["video_id"]
    assert video_id is not None
    assert upload_json["status"] == "UPLOADED"

    # Wait for background metadata extraction from video.uploaded event
    message_broker.in_memory.wait_for_idle(timeout=3.0)

    # 2. Check metadata service stored video metadata
    meta_res = metadata_client.get(f"/api/v1/videos/{video_id}")
    assert meta_res.status_code == 200
    meta_json = meta_res.json()
    assert meta_json["video_id"] == video_id
    assert meta_json["title"] == "Nature Walk 4K"

    # 3. Trigger processing orchestrator
    proc_res = orchestrator_client.post(
        f"/api/v1/process/{video_id}",
        json={"resolutions": ["360p", "720p", "1080p"]},
    )
    assert proc_res.status_code == 202
    job_id = proc_res.json()["id"]

    # Wait for asynchronous transcode and thumbnail workers to complete
    message_broker.in_memory.wait_for_idle(timeout=5.0)

    # 4. Check initial job status
    status_res = orchestrator_client.get(f"/api/v1/status/{video_id}")
    assert status_res.status_code == 200
    assert status_res.json()["status"] in ("IN_PROGRESS", "COMPLETED")

    # 5. Verify and check available outputs from Media Delivery Service
    outputs_res = media_client.get(f"/api/v1/outputs/{video_id}")
    assert outputs_res.status_code == 200
    outputs = outputs_res.json()
    assert len(outputs) == 3
    resolutions = [o["resolution"] for o in outputs]
    assert "360p" in resolutions
    assert "720p" in resolutions
    assert "1080p" in resolutions

    # 6. Test HTTP 206 Partial Content Range streaming
    stream_res = media_client.get(
        f"/media/videos/{video_id}/720p",
        headers={"Range": "bytes=0-50"},
    )
    assert stream_res.status_code == 206
    assert "Content-Range" in stream_res.headers
    assert stream_res.headers["Content-Range"].startswith("bytes 0-50/")
    assert len(stream_res.content) == 51

    # 7. Check Thumbnails API
    thumbs_res = thumbnail_client.get(f"/api/v1/thumbnails/{video_id}")
    assert thumbs_res.status_code == 200
    assert len(thumbs_res.json()) >= 1

    # 8. Final job status verification (100% completed)
    final_job_res = orchestrator_client.get(f"/api/v1/jobs/{job_id}")
    assert final_job_res.status_code == 200
    final_job = final_job_res.json()
    assert final_job["status"] == "COMPLETED"
    assert final_job["progress_percent"] == 100
    assert final_job["thumbnail_status"] == "COMPLETED"
