import os
import uuid
from shared.events import TranscodeTaskEvent
from shared.messaging import message_broker
from services.transcoding_worker.src.worker import process_transcode_task
from services.transcoding_worker.src.db import SessionLocal
from services.transcoding_worker.src.models import TranscodingOutput

def test_prevent_duplicate_message_processing(valid_mp4_bytes):
    video_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    upload_dir = os.path.join(os.environ.get("DATA_DIR", "/tmp"), "uploads", video_id)
    os.makedirs(upload_dir, exist_ok=True)
    source_path = os.path.join(upload_dir, "raw_dup_test.mp4")
    with open(source_path, "wb") as f:
        f.write(valid_mp4_bytes)

    task = TranscodeTaskEvent(
        job_id=job_id,
        video_id=video_id,
        source_file_path=source_path,
        resolution="720p",
        attempt_number=1,
    )
    task_json = task.to_json()

    # Deliver first time
    process_transcode_task("job.transcode", task_json)

    # Deliver second time (duplicate redelivery simulation)
    process_transcode_task("job.transcode", task_json)

    # Deliver third time
    process_transcode_task("job.transcode", task_json)

    # Verify that only ONE output record was created in transcoding_outputs table
    with SessionLocal() as db:
        outputs = db.query(TranscodingOutput).filter(
            TranscodingOutput.video_id == video_id,
            TranscodingOutput.resolution == "720p",
        ).all()
        assert len(outputs) == 1
        assert outputs[0].resolution == "720p"
        assert outputs[0].video_id == video_id
