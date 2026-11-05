import os
from pydantic_settings import BaseSettings
from shared.config import shared_settings

class MediaDeliverySettings(BaseSettings):
    SERVICE_NAME: str = "media-delivery-service"
    PORT: int = 8006
    TRANSCODING_SERVICE_URL: str = os.getenv("TRANSCODING_SERVICE_URL", "http://localhost:8004")
    THUMBNAIL_SERVICE_URL: str = os.getenv("THUMBNAIL_SERVICE_URL", "http://localhost:8005")

    class Config:
        env_file = ".env"
        extra = "allow"

media_settings = MediaDeliverySettings()
