import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.transcoding_orchestrator.src.db import init_db, SessionLocal
from services.transcoding_orchestrator.src.routes import router
from services.transcoding_orchestrator.src.orchestrator import (
    TranscodingOrchestrator,
    handle_transcode_completed,
    handle_transcode_failed,
    handle_thumbnail_completed,
    handle_thumbnail_failed,
)
from shared.messaging import message_broker

logger = logging.getLogger("orchestrator_main")

def handle_video_uploaded_autostart(routing_key: str, body_str: str):
    """
    Auto-triggers processing job on video upload.
    """
    try:
        data = json.loads(body_str)
        video_id = data.get("video_id")
        if video_id:
            with SessionLocal() as db:
                TranscodingOrchestrator.start_processing(video_id, db)
                logger.info(f"Auto-started processing for uploaded video: {video_id}")
    except Exception as e:
        logger.error(f"Error auto-starting processing for uploaded video: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Subscribe to RabbitMQ events
    message_broker.subscribe("video.uploaded", handle_video_uploaded_autostart)
    message_broker.subscribe("event.transcode.completed", handle_transcode_completed)
    message_broker.subscribe("event.transcode.failed", handle_transcode_failed)
    message_broker.subscribe("event.thumbnail.completed", handle_thumbnail_completed)
    message_broker.subscribe("event.thumbnail.failed", handle_thumbnail_failed)
    yield

app = FastAPI(
    title="Transcoding Orchestrator Service",
    version="1.0.0",
    description="Microservice responsible for coordinating multi-resolution transcoding jobs, retries, and dead-letter handling.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "transcoding-orchestrator-service"}
