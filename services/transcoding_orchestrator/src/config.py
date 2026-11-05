import os
from pydantic_settings import BaseSettings
from shared.config import shared_settings

class OrchestratorSettings(BaseSettings):
    SERVICE_NAME: str = "transcoding-orchestrator-service"
    PORT: int = 8003
    DATABASE_URL: str = os.getenv(
        "ORCHESTRATOR_DATABASE_URL",
        f"sqlite:///{os.path.join(shared_settings.DBS_DIR, 'orchestrator.db')}"
    )
    METADATA_SERVICE_URL: str = os.getenv("METADATA_SERVICE_URL", "http://localhost:8002")

    class Config:
        env_file = ".env"
        extra = "allow"

orchestrator_settings = OrchestratorSettings()
