import datetime
import json
import logging
import time
from typing import Optional
import redis
from services.transcoding_worker.src.db import SessionLocal
from services.transcoding_worker.src.models import ProcessingAttempt, TranscodingOutput
from services.transcoding_worker.src.ffmpeg_transcoder import FFmpegTranscoder
from shared.config import shared_settings
from shared.events import (
    TranscodeCompletedEvent,
    TranscodeFailedEvent,
)
from shared.messaging import message_broker
from shared.storage import StorageManager

logger = logging.getLogger("transcoding_worker")

# Local in-memory lock fallback when Redis is absent
_in_memory_locks = set()

class WorkerDeduplicator:
    @staticmethod
    def get_redis_client() -> Optional[redis.Redis]:
        if shared_settings.USE_IN_MEMORY_BROKER:
            return None
        try:
            r = redis.Redis(
                host=shared_settings.REDIS_HOST,
                port=shared_settings.REDIS_PORT,
                db=shared_settings.REDIS_DB,
                password=shared_settings.REDIS_PASSWORD,
                socket_timeout=1,
            )
            r.ping()
            return r
        except Exception:
            return None

    @classmethod
    def acquire_lock(cls, key: str, ttl_seconds: int = 600) -> bool:
        r = cls.get_redis_client()
        if r:
            acquired = r.set(f"lock:{key}", "1", nx=True, ex=ttl_seconds)
            return bool(acquired)
        else:
            if key in _in_memory_locks:
                return False
            _in_memory_locks.add(key)
            return True

    @classmethod
    def release_lock(cls, key: str):
        r = cls.get_redis_client()
        if r:
            try:
                r.delete(f"lock:{key}")
            except Exception:
                pass
        else:
            _in_memory_locks.discard(key)


def process_transcode_task(routing_key: str, body_str: str):
    """
    Message consumer for job.transcode messages.
    Idempotent: prevents duplicate processing if message is delivered more than once.
    """
    try:
        data = json.loads(body_str)
        job_id = data.get("job_id")
        video_id = data.get("video_id")
        source_path = data.get("source_file_path")
        resolution = data.get("resolution")
        attempt_number = data.get("attempt_number", 1)

        if not (job_id and video_id and source_path and resolution):
            logger.error(f"Malformed transcode task: {body_str}")
            return

        dedup_key = f"transcode:{video_id}:{resolution}"

        with SessionLocal() as db:
            # 1. Check if output already exists (Idempotency Check)
            existing_output = db.query(TranscodingOutput).filter(
                TranscodingOutput.video_id == video_id,
                TranscodingOutput.resolution == resolution,
            ).first()

            if existing_output:
                logger.info(f"[Deduplication] Output already exists for video {video_id} @ {resolution}. Skipping duplicate processing.")
                # Notify orchestrator of completion without reprocessing
                comp_event = TranscodeCompletedEvent(
                    job_id=job_id,
                    video_id=video_id,
                    resolution=resolution,
                    output_id=existing_output.id,
                    file_path=existing_output.file_path,
                    file_size=existing_output.file_size,
                    width=existing_output.width,
                    height=existing_output.height,
                    bitrate=existing_output.bitrate,
                    duration_seconds=0.0,
                )
                message_broker.publish_event("event.transcode.completed", comp_event)
                return

            # 2. Acquire lock to prevent concurrent duplicate execution
            if not WorkerDeduplicator.acquire_lock(dedup_key):
                logger.warning(f"[Deduplication] Task currently in-flight for {dedup_key}. Skipping duplicate message delivery.")
                return

            # 3. Record attempt: STARTED
            attempt = ProcessingAttempt(
                job_id=job_id,
                video_id=video_id,
                resolution=resolution,
                attempt_number=attempt_number,
                status="STARTED",
            )
            db.add(attempt)
            db.commit()
            db.refresh(attempt)

            output_file = StorageManager.get_transcoded_path(video_id, resolution)

            try:
                # 4. Execute FFmpeg transcode
                res_data = FFmpegTranscoder.transcode(source_path, output_file, resolution)

                # 5. Record attempt: SUCCESS
                attempt.status = "SUCCESS"
                attempt.duration_seconds = res_data["duration_seconds"]
                attempt.completed_at = datetime.datetime.utcnow()

                # 6. Save transcoding output record
                output_record = TranscodingOutput(
                    video_id=video_id,
                    job_id=job_id,
                    resolution=resolution,
                    width=res_data["width"],
                    height=res_data["height"],
                    file_path=res_data["file_path"],
                    file_size=res_data["file_size"],
                    bitrate=res_data["bitrate"],
                    format="mp4",
                )
                db.add(output_record)
                db.commit()
                db.refresh(output_record)

                # 7. Publish completion event
                comp_event = TranscodeCompletedEvent(
                    job_id=job_id,
                    video_id=video_id,
                    resolution=resolution,
                    output_id=output_record.id,
                    file_path=output_record.file_path,
                    file_size=output_record.file_size,
                    width=output_record.width,
                    height=output_record.height,
                    bitrate=output_record.bitrate,
                    duration_seconds=res_data["duration_seconds"],
                )
                message_broker.publish_event("event.transcode.completed", comp_event)
                logger.info(f"Transcoded video {video_id} to {resolution} successfully.")

            except Exception as e:
                # 8. Record attempt: FAILED
                logger.error(f"Transcoding error on video {video_id} @ {resolution}: {e}")
                attempt.status = "FAILED"
                attempt.error_details = str(e)
                attempt.completed_at = datetime.datetime.utcnow()
                db.commit()

                # Release lock so retry can acquire
                WorkerDeduplicator.release_lock(dedup_key)

                # 9. Publish failure event
                fail_event = TranscodeFailedEvent(
                    job_id=job_id,
                    video_id=video_id,
                    resolution=resolution,
                    attempt_number=attempt_number,
                    error_message=str(e),
                )
                message_broker.publish_event("event.transcode.failed", fail_event)

    except Exception as exc:
        logger.error(f"Fatal worker error in process_transcode_task: {exc}")
