import json
import logging
import uuid
from services.thumbnail_generation.src.db import SessionLocal
from services.thumbnail_generation.src.models import VideoThumbnail
from services.thumbnail_generation.src.ffmpeg_thumbnail import FFmpegThumbnailGenerator
from shared.events import (
    ThumbnailCompletedEvent,
    ThumbnailFailedEvent,
)
from shared.messaging import message_broker
from shared.storage import StorageManager

logger = logging.getLogger("thumbnail_worker")

def process_thumbnail_task(routing_key: str, body_str: str):
    """
    Consumer callback for job.thumbnail.
    """
    try:
        data = json.loads(body_str)
        job_id = data.get("job_id")
        video_id = data.get("video_id")
        source_path = data.get("source_file_path")
        time_offset = float(data.get("time_offset_seconds", 1.0))

        if not (job_id and video_id and source_path):
            return

        with SessionLocal() as db:
            # Check for existing completed thumbnail
            existing = db.query(VideoThumbnail).filter(
                VideoThumbnail.video_id == video_id,
                VideoThumbnail.status == "COMPLETED"
            ).first()

            if existing:
                logger.info(f"Thumbnail already generated for video {video_id}. Re-emitting completion.")
                event = ThumbnailCompletedEvent(
                    job_id=job_id,
                    video_id=video_id,
                    thumbnail_id=existing.id,
                    file_path=existing.file_path,
                    file_size=existing.file_size,
                    width=existing.width,
                    height=existing.height,
                )
                message_broker.publish_event("event.thumbnail.completed", event)
                return

            thumbnail_id = str(uuid.uuid4())
            output_path = StorageManager.get_thumbnail_path(video_id, thumbnail_id)

            record = VideoThumbnail(
                id=thumbnail_id,
                video_id=video_id,
                file_path=output_path,
                time_offset_seconds=time_offset,
                status="PENDING",
            )
            db.add(record)
            db.commit()

            try:
                thumb_data = FFmpegThumbnailGenerator.generate(source_path, output_path, time_offset)
                record.status = "COMPLETED"
                record.file_size = thumb_data["file_size"]
                record.width = thumb_data["width"]
                record.height = thumb_data["height"]
                db.commit()

                event = ThumbnailCompletedEvent(
                    job_id=job_id,
                    video_id=video_id,
                    thumbnail_id=record.id,
                    file_path=record.file_path,
                    file_size=record.file_size,
                    width=record.width,
                    height=record.height,
                )
                message_broker.publish_event("event.thumbnail.completed", event)
                logger.info(f"Generated thumbnail for video {video_id} successfully.")

            except Exception as e:
                logger.error(f"Failed to generate thumbnail for video {video_id}: {e}")
                record.status = "FAILED"
                record.error_message = str(e)
                db.commit()

                fail_event = ThumbnailFailedEvent(
                    job_id=job_id,
                    video_id=video_id,
                    error_message=str(e),
                )
                message_broker.publish_event("event.thumbnail.failed", fail_event)

    except Exception as exc:
        logger.error(f"Fatal thumbnail worker error: {exc}")
