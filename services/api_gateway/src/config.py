import os
from pydantic_settings import BaseSettings

class GatewaySettings(BaseSettings):
    SERVICE_NAME: str = "api-gateway"
    PORT: int = 8000

    # Downstream service URLs
    UPLOAD_SERVICE_URL: str = os.getenv("UPLOAD_SERVICE_URL", "http://localhost:8001")
    METADATA_SERVICE_URL: str = os.getenv("METADATA_SERVICE_URL", "http://localhost:8002")
    ORCHESTRATOR_SERVICE_URL: str = os.getenv("ORCHESTRATOR_SERVICE_URL", "http://localhost:8003")
    TRANSCODING_SERVICE_URL: str = os.getenv("TRANSCODING_SERVICE_URL", "http://localhost:8004")
    THUMBNAIL_SERVICE_URL: str = os.getenv("THUMBNAIL_SERVICE_URL", "http://localhost:8005")
    MEDIA_SERVICE_URL: str = os.getenv("MEDIA_SERVICE_URL", "http://localhost:8006")

    class Config:
        env_file = ".env"
        extra = "allow"

gateway_settings = GatewaySettings()
