import os
from pydantic_settings import BaseSettings
from shared.config import shared_settings

class WorkerSettings(BaseSettings):
    SERVICE_NAME: str = "transcoding-worker-service"
    PORT: int = 8004
    DATABASE_URL: str = os.getenv(
        "TRANSCODING_DATABASE_URL",
        f"sqlite:///{os.path.join(shared_settings.DBS_DIR, 'transcoding.db')}"
    )

    class Config:
        env_file = ".env"
        extra = "allow"

worker_settings = WorkerSettings()
