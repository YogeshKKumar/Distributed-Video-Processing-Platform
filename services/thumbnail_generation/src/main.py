from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.thumbnail_generation.src.db import init_db
from services.thumbnail_generation.src.routes import router
from services.thumbnail_generation.src.worker import process_thumbnail_task
from shared.config import shared_settings
from shared.messaging import message_broker

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Subscribe to thumbnail job events
    message_broker.subscribe(shared_settings.ROUTING_KEY_THUMBNAIL, process_thumbnail_task)
    yield

app = FastAPI(
    title="Thumbnail Generation Service",
    version="1.0.0",
    description="Microservice responsible for extracting and serving preview thumbnails from uploaded videos.",
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
    return {"status": "healthy", "service": "thumbnail-generation-service"}
