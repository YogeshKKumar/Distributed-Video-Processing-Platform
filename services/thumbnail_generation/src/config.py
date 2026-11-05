import os
from pydantic_settings import BaseSettings
from shared.config import shared_settings

class ThumbnailSettings(BaseSettings):
    SERVICE_NAME: str = "thumbnail-generation-service"
    PORT: int = 8005
    DATABASE_URL: str = os.getenv(
        "THUMBNAIL_DATABASE_URL",
        f"sqlite:///{os.path.join(shared_settings.DBS_DIR, 'thumbnail.db')}"
    )

    class Config:
        env_file = ".env"
        extra = "allow"

thumbnail_settings = ThumbnailSettings()
