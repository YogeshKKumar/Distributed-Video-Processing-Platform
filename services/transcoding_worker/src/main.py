from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
try:
    from .db import init_db, get_db
    from .models import ProcessingAttempt, TranscodingOutput
    from .worker import process_transcode_task
except (ImportError, ValueError):
    try:
        from src.db import init_db, get_db
        from src.models import ProcessingAttempt, TranscodingOutput
        from src.worker import process_transcode_task
    except (ImportError, ValueError):
        from services.transcoding_worker.src.db import init_db, get_db
        from services.transcoding_worker.src.models import ProcessingAttempt, TranscodingOutput
        from services.transcoding_worker.src.worker import process_transcode_task
from shared.config import shared_settings
from shared.messaging import message_broker

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Subscribe to RabbitMQ transcoding jobs
    message_broker.subscribe(shared_settings.ROUTING_KEY_TRANSCODE, process_transcode_task)
    yield

app = FastAPI(
    title="Video Transcoding Worker Service",
    version="1.0.0",
    description="Worker service that consumes transcode tasks, runs FFmpeg, prevents duplicate processing, and tracks attempts.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "transcoding-worker-service"}

@app.get("/api/v1/outputs/{video_id}", tags=["Outputs"])
def get_video_outputs(video_id: str, db: Session = Depends(get_db)):
    outputs = db.query(TranscodingOutput).filter(TranscodingOutput.video_id == video_id).all()
    return [o.to_dict() for o in outputs]

@app.get("/api/v1/attempts/{video_id}", tags=["Attempts"])
def get_video_attempts(video_id: str, db: Session = Depends(get_db)):
    attempts = db.query(ProcessingAttempt).filter(ProcessingAttempt.video_id == video_id).order_by(ProcessingAttempt.started_at.desc()).all()
    return [a.to_dict() for a in attempts]
