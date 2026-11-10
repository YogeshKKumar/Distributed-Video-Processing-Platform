import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from .db import init_db
    from .routes import (
        router,
        handle_video_uploaded,
        handle_job_status_updated,
    )
except (ImportError, ValueError):
    try:
        from src.db import init_db
        from src.routes import (
            router,
            handle_video_uploaded,
            handle_job_status_updated,
        )
    except (ImportError, ValueError):
        from services.video_metadata.src.db import init_db
        from services.video_metadata.src.routes import (
            router,
            handle_video_uploaded,
            handle_job_status_updated,
        )
from shared.messaging import message_broker

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Subscribe to RabbitMQ events
    message_broker.subscribe("video.uploaded", handle_video_uploaded)
    message_broker.subscribe("event.job.status_updated", handle_job_status_updated)
    yield

app = FastAPI(
    title="Video Metadata Service",
    version="1.0.0",
    description="Microservice for storing video metadata, dimensions, duration, format, and processing status.",
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
    return {"status": "healthy", "service": "video-metadata-service"}
