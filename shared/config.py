import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Base data directory
DEFAULT_DATA_DIR = os.getenv("DATA_DIR", str(Path(__file__).resolve().parent.parent / "data"))

class ResolutionConfig:
    RESOLUTIONS = {
        "360p": {
            "name": "360p",
            "width": 640,
            "height": 360,
            "video_bitrate": "800k",
            "audio_bitrate": "96k",
            "crf": "26",
            "preset": "fast",
        },
        "720p": {
            "name": "720p",
            "width": 1280,
            "height": 720,
            "video_bitrate": "2500k",
            "audio_bitrate": "128k",
            "crf": "23",
            "preset": "fast",
        },
        "1080p": {
            "name": "1080p",
            "width": 1920,
            "height": 1080,
            "video_bitrate": "4500k",
            "audio_bitrate": "192k",
            "crf": "21",
            "preset": "fast",
        },
    }

class Settings(BaseSettings):
    # Base paths
    DATA_DIR: str = DEFAULT_DATA_DIR
    UPLOAD_DIR: str = os.path.join(DEFAULT_DATA_DIR, "uploads")
    TRANSCODED_DIR: str = os.path.join(DEFAULT_DATA_DIR, "transcoded")
    THUMBNAILS_DIR: str = os.path.join(DEFAULT_DATA_DIR, "thumbnails")
    DBS_DIR: str = os.path.join(DEFAULT_DATA_DIR, "dbs")

    # Upload constraints
    MAX_UPLOAD_SIZE_BYTES: int = 500 * 1024 * 1024  # 500 MB
    ALLOWED_EXTENSIONS: list[str] = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    ALLOWED_MIME_TYPES: list[str] = [
        "video/mp4",
        "video/quicktime",
        "video/x-msvideo",
        "video/x-matroska",
        "video/webm",
        "application/octet-stream", # Some clients upload raw video as octet-stream
    ]

    # RabbitMQ Settings
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    EXCHANGE_NAME: str = "video.exchange"
    DLX_EXCHANGE_NAME: str = "video.dlx"
    
    # Queues
    TRANSCODING_QUEUE: str = "transcoding.jobs.queue"
    THUMBNAIL_QUEUE: str = "thumbnail.jobs.queue"
    EVENTS_QUEUE: str = "transcoding.events.queue"
    DLQ_QUEUE: str = "transcoding.dlq"

    # Routing Keys
    ROUTING_KEY_TRANSCODE: str = "job.transcode"
    ROUTING_KEY_THUMBNAIL: str = "job.thumbnail"
    ROUTING_KEY_EVENT_PREFIX: str = "event."

    # Redis Settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str | None = os.getenv("REDIS_PASSWORD", None)

    # Worker limits
    MAX_JOB_RETRIES: int = 3
    DEFAULT_RESOLUTIONS: list[str] = ["360p", "720p", "1080p"]

    # Testing & Standalone Flag (defaults to in-memory broker if not running inside docker container)
    USE_IN_MEMORY_BROKER: bool = os.getenv(
        "USE_IN_MEMORY_BROKER",
        "true" if os.getenv("RABBITMQ_HOST") in (None, "localhost", "") else "false"
    ).lower() in ("true", "1", "yes")

    class Config:
        env_file = ".env"
        extra = "allow"

shared_settings = Settings()

# Ensure directories exist
for path in [
    shared_settings.DATA_DIR,
    shared_settings.UPLOAD_DIR,
    shared_settings.TRANSCODED_DIR,
    shared_settings.THUMBNAILS_DIR,
    shared_settings.DBS_DIR,
]:
    os.makedirs(path, exist_ok=True)
