import glob
import json
import logging
import os
from typing import List, Optional
from sqlalchemy.orm import Session
from services.transcoding_orchestrator.src.db import SessionLocal
from services.transcoding_orchestrator.src.models import ProcessingJob
from shared.config import shared_settings
from shared.events import (
    TranscodeTaskEvent,
    ThumbnailTaskEvent,
    JobStatusUpdatedEvent,
)
from shared.messaging import message_broker

logger = logging.getLogger("orchestrator")

class TranscodingOrchestrator:
    @staticmethod
    def find_source_video(video_id: str) -> Optional[str]:
        upload_folder = os.path.join(shared_settings.UPLOAD_DIR, video_id)
        if not os.path.exists(upload_folder):
            return None
        matches = glob.glob(os.path.join(upload_folder, "*"))
        return matches[0] if matches else None

    @classmethod
    def start_processing(
        cls,
        video_id: str,
        db: Session,
        resolutions: Optional[List[str]] = None,
    ) -> ProcessingJob:
        target_res = resolutions or shared_settings.DEFAULT_RESOLUTIONS
        source_path = cls.find_source_video(video_id)
        if not source_path or not os.path.exists(source_path):
            raise FileNotFoundError(f"Source video file not found for video {video_id}")

        # Check existing job or create new
        job = db.query(ProcessingJob).filter(ProcessingJob.video_id == video_id).order_by(ProcessingJob.created_at.desc()).first()
        if not job or job.status in ("COMPLETED", "FAILED"):
            job = ProcessingJob(
                video_id=video_id,
                status="IN_PROGRESS",
                retry_count=0,
                max_retries=shared_settings.MAX_JOB_RETRIES,
                error_message=None,
            )
            job.set_target_resolutions_list(target_res)
            job.set_completed_resolutions_list([])
            job.thumbnail_status = "PENDING"
            db.add(job)
        else:
            # Retrying active or failed job
            job.status = "IN_PROGRESS"
            job.set_target_resolutions_list(target_res)
            job.error_message = None

        db.commit()
        db.refresh(job)

        # 1. Publish transcode tasks for each target resolution
        for res in target_res:
            task = TranscodeTaskEvent(
                job_id=job.id,
                video_id=video_id,
                source_file_path=source_path,
                resolution=res,
                attempt_number=job.retry_count + 1,
                max_retries=job.max_retries,
            )
            message_broker.publish_event(shared_settings.ROUTING_KEY_TRANSCODE, task)

        # 2. Publish thumbnail task
        thumb_task = ThumbnailTaskEvent(
            job_id=job.id,
            video_id=video_id,
            source_file_path=source_path,
            time_offset_seconds=1.0,
        )
        message_broker.publish_event(shared_settings.ROUTING_KEY_THUMBNAIL, thumb_task)

        # 3. Notify listeners
        status_event = JobStatusUpdatedEvent(
            job_id=job.id,
            video_id=video_id,
            status="IN_PROGRESS",
            completed_resolutions=job.get_completed_resolutions_list(),
            thumbnail_status=job.thumbnail_status,
        )
        message_broker.publish_event("event.job.status_updated", status_event)
        logger.info(f"Dispatched processing job {job.id} for video {video_id} with resolutions {target_res}")
        return job

    @classmethod
    def check_and_complete_job(cls, job: ProcessingJob, db: Session):
        targets = set(job.get_target_resolutions_list())
        completed = set(job.get_completed_resolutions_list())

        if targets.issubset(completed) and job.thumbnail_status == "COMPLETED":
            job.status = "COMPLETED"
            job.error_message = None
            db.commit()
            db.refresh(job)

            status_event = JobStatusUpdatedEvent(
                job_id=job.id,
                video_id=job.video_id,
                status="COMPLETED",
                completed_resolutions=job.get_completed_resolutions_list(),
                thumbnail_status=job.thumbnail_status,
            )
            message_broker.publish_event("event.job.status_updated", status_event)
            logger.info(f"Processing job {job.id} for video {job.video_id} successfully COMPLETED.")


def handle_transcode_completed(routing_key: str, body_str: str):
    try:
        data = json.loads(body_str)
        job_id = data.get("job_id")
        resolution = data.get("resolution")

        with SessionLocal() as db:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if not job:
                return

            completed = job.get_completed_resolutions_list()
            if resolution and resolution not in completed:
                completed.append(resolution)
                job.set_completed_resolutions_list(completed)
                db.commit()

            TranscodingOrchestrator.check_and_complete_job(job, db)
    except Exception as e:
        logger.error(f"Error handling transcode completed event: {e}")


def handle_transcode_failed(routing_key: str, body_str: str):
    try:
        data = json.loads(body_str)
        job_id = data.get("job_id")
        video_id = data.get("video_id")
        resolution = data.get("resolution")
        error_msg = data.get("error_message", "Unknown transcoding failure")

        with SessionLocal() as db:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if not job:
                return

            job.retry_count += 1
            if job.retry_count < job.max_retries:
                # Re-queue retry
                job.status = "RETRYING"
                job.error_message = f"Attempt {job.retry_count} failed for {resolution}: {error_msg}. Retrying..."
                db.commit()

                source_path = TranscodingOrchestrator.find_source_video(video_id)
                if source_path:
                    retry_task = TranscodeTaskEvent(
                        job_id=job.id,
                        video_id=video_id,
                        source_file_path=source_path,
                        resolution=resolution,
                        attempt_number=job.retry_count + 1,
                        max_retries=job.max_retries,
                    )
                    message_broker.publish_event(shared_settings.ROUTING_KEY_TRANSCODE, retry_task)
                    logger.warning(f"Re-enqueued transcode retry for {resolution} (Attempt {job.retry_count + 1})")
            else:
                # Exceeded max retries -> Dead Letter Handling
                job.status = "FAILED"
                job.error_message = f"Transcoding failed for {resolution} after {job.retry_count} attempts: {error_msg}"
                db.commit()

                message_broker.publish_dlq(routing_key, body_str, job.error_message)
                logger.error(f"Job {job.id} failed permanently and sent to DLQ. Error: {job.error_message}")

                # Notify listeners
                status_event = JobStatusUpdatedEvent(
                    job_id=job.id,
                    video_id=video_id,
                    status="FAILED",
                    completed_resolutions=job.get_completed_resolutions_list(),
                    thumbnail_status=job.thumbnail_status,
                    error_message=job.error_message,
                )
                message_broker.publish_event("event.job.status_updated", status_event)
    except Exception as e:
        logger.error(f"Error handling transcode failed event: {e}")


def handle_thumbnail_completed(routing_key: str, body_str: str):
    try:
        data = json.loads(body_str)
        job_id = data.get("job_id")
        with SessionLocal() as db:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if not job:
                return
            job.thumbnail_status = "COMPLETED"
            db.commit()
            TranscodingOrchestrator.check_and_complete_job(job, db)
    except Exception as e:
        logger.error(f"Error handling thumbnail completed event: {e}")


def handle_thumbnail_failed(routing_key: str, body_str: str):
    try:
        data = json.loads(body_str)
        job_id = data.get("job_id")
        error_msg = data.get("error_message", "Thumbnail creation failed")
        with SessionLocal() as db:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if not job:
                return
            job.thumbnail_status = "FAILED"
            job.error_message = (job.error_message or "") + f" [Thumbnail: {error_msg}]"
            db.commit()
    except Exception as e:
        logger.error(f"Error handling thumbnail failed event: {e}")
