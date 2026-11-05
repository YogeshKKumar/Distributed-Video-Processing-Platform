import os
from pydantic_settings import BaseSettings
from shared.config import shared_settings

class MetadataSettings(BaseSettings):
    SERVICE_NAME: str = "video-metadata-service"
    PORT: int = 8002
    DATABASE_URL: str = os.getenv(
        "METADATA_DATABASE_URL",
        f"sqlite:///{os.path.join(shared_settings.DBS_DIR, 'metadata.db')}"
    )

    class Config:
        env_file = ".env"
        extra = "allow"

metadata_settings = MetadataSettings()
