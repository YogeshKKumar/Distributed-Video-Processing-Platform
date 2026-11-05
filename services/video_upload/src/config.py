import os
from pydantic_settings import BaseSettings
from shared.config import shared_settings

class UploadSettings(BaseSettings):
    SERVICE_NAME: str = "video-upload-service"
    PORT: int = 8001
    DATABASE_URL: str = os.getenv(
        "UPLOAD_DATABASE_URL",
        f"sqlite:///{os.path.join(shared_settings.DBS_DIR, 'upload.db')}"
    )

    class Config:
        env_file = ".env"
        extra = "allow"

upload_settings = UploadSettings()
