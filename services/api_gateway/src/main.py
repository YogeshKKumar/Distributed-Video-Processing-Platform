from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
try:
    from .routes import router
except (ImportError, ValueError):
    try:
        from src.routes import router
    except (ImportError, ValueError):
        from services.api_gateway.src.routes import router

app = FastAPI(
    title="Distributed Video Processing Platform - API Gateway",
    version="1.0.0",
    description="Unified API Gateway routing requests to independently deployable microservices.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "Accept-Ranges", "Content-Length"],
)

app.include_router(router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal Gateway Error: {str(exc)}"},
    )

@app.get("/health", tags=["Health"])
def gateway_health():
    return {"status": "healthy", "service": "api-gateway"}
