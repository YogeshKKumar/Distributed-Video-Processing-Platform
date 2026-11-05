import os
import uuid
import json
from shared.events import TranscodeTaskEvent, TranscodeFailedEvent
from shared.messaging import message_broker
from services.transcoding_worker.src.worker import process_transcode_task
from services.transcoding_orchestrator.src.db import SessionLocal as OrchSessionLocal
from services.transcoding_orchestrator.src.models import ProcessingJob
from services.transcoding_orchestrator.src.orchestrator import handle_transcode_failed

def test_worker_failure_recording_and_retry_limit():
    video_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    # Create job with max_retries = 3
    with OrchSessionLocal() as db:
        job = ProcessingJob(
            id=job_id,
            video_id=video_id,
            status="IN_PROGRESS",
            retry_count=0,
            max_retries=3,
        )
        job.set_target_resolutions_list(["1080p"])
        db.add(job)
        db.commit()

    # Intentionally provide a non-existent source path to induce worker failure
    task = TranscodeTaskEvent(
        job_id=job_id,
        video_id=video_id,
        source_file_path="/tmp/non_existent_corrupted_file.mp4",
        resolution="1080p",
        attempt_number=1,
    )

    # Process task (Attempt 1 fails)
    process_transcode_task("job.transcode", task.to_json())
    message_broker.in_memory.wait_for_idle(timeout=2.0)

    with OrchSessionLocal() as db:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        assert job.retry_count == 1
        assert job.status == "RETRYING"

    # Simulate Attempt 2 failure
    fail_event_2 = TranscodeFailedEvent(
        job_id=job_id,
        video_id=video_id,
        resolution="1080p",
        attempt_number=2,
        error_message="Simulation failure attempt 2",
    )
    handle_transcode_failed("event.transcode.failed", fail_event_2.to_json())
    message_broker.in_memory.wait_for_idle(timeout=2.0)

    with OrchSessionLocal() as db:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        assert job.retry_count == 2
        assert job.status == "RETRYING"

    # Simulate Attempt 3 failure (max retries reached -> DLQ)
    fail_event_3 = TranscodeFailedEvent(
        job_id=job_id,
        video_id=video_id,
        resolution="1080p",
        attempt_number=3,
        error_message="Simulation failure attempt 3",
    )
    handle_transcode_failed("event.transcode.failed", fail_event_3.to_json())
    message_broker.in_memory.wait_for_idle(timeout=2.0)

    with OrchSessionLocal() as db:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        assert job.retry_count == 3
        assert job.status == "FAILED"
        assert "Transcoding failed for 1080p" in job.error_message

    # Verify message was sent to Dead Letter Queue (DLQ)
    dlq_messages = message_broker.in_memory.get_dlq_messages()
    assert len(dlq_messages) >= 1
    assert any("Simulation failure attempt 3" in m["error"] for m in dlq_messages)
