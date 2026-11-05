import json
import time
from typing import Any, Optional
from pydantic import BaseModel, Field

class BaseEvent(BaseModel):
    event_type: str
    timestamp: float = Field(default_factory=time.time)

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "BaseEvent":
        data = json.loads(json_str)
        return cls(**data)


class VideoUploadedEvent(BaseEvent):
    event_type: str = "video.uploaded"
    video_id: str
    filename: str
    file_path: str
    file_size: int
    content_type: str
    title: Optional[str] = None


class TranscodeTaskEvent(BaseEvent):
    event_type: str = "job.transcode"
    job_id: str
    video_id: str
    source_file_path: str
    resolution: str  # e.g., '360p', '720p', '1080p'
    attempt_number: int = 1
    max_retries: int = 3


class ThumbnailTaskEvent(BaseEvent):
    event_type: str = "job.thumbnail"
    job_id: str
    video_id: str
    source_file_path: str
    time_offset_seconds: float = 1.0


class TranscodeCompletedEvent(BaseEvent):
    event_type: str = "event.transcode.completed"
    job_id: str
    video_id: str
    resolution: str
    output_id: str
    file_path: str
    file_size: int
    width: int
    height: int
    bitrate: int
    duration_seconds: float


class TranscodeFailedEvent(BaseEvent):
    event_type: str = "event.transcode.failed"
    job_id: str
    video_id: str
    resolution: str
    attempt_number: int
    error_message: str


class ThumbnailCompletedEvent(BaseEvent):
    event_type: str = "event.thumbnail.completed"
    job_id: str
    video_id: str
    thumbnail_id: str
    file_path: str
    file_size: int
    width: int
    height: int


class ThumbnailFailedEvent(BaseEvent):
    event_type: str = "event.thumbnail.failed"
    job_id: str
    video_id: str
    error_message: str


class JobStatusUpdatedEvent(BaseEvent):
    event_type: str = "event.job.status_updated"
    job_id: str
    video_id: str
    status: str
    completed_resolutions: list[str] = []
    thumbnail_status: str = "PENDING"
    error_message: Optional[str] = None
