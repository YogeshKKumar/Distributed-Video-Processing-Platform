from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from .db import init_db
    from .routes import router
except (ImportError, ValueError):
    try:
        from src.db import init_db
        from src.routes import router
    except (ImportError, ValueError):
        from services.video_upload.src.db import init_db
        from services.video_upload.src.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Video Upload Service",
    version="1.0.0",
    description="Microservice responsible for accepting video uploads, validating formats/sizes, and emitting upload events.",
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
    return {"status": "healthy", "service": "video-upload-service"}
