from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from .routes import router
except (ImportError, ValueError):
    try:
        from src.routes import router
    except (ImportError, ValueError):
        from services.media_delivery.src.routes import router

app = FastAPI(
    title="Media Delivery Service",
    version="1.0.0",
    description="Microservice responsible for secure video streaming (HTTP 206 partial content) and thumbnail delivery.",
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
    return {"status": "healthy", "service": "media-delivery-service"}
