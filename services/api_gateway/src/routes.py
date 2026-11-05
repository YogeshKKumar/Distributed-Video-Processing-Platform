import asyncio
import logging
from typing import Optional
import httpx
from fastapi import APIRouter, Request, Response, UploadFile, File, Form, HTTPException, status
from fastapi.responses import StreamingResponse
from services.api_gateway.src.config import gateway_settings

logger = logging.getLogger("api_gateway")
router = APIRouter()

# ----------------- VIDEO UPLOADS -----------------

@router.post("/videos/upload", status_code=status.HTTP_201_CREATED, tags=["Videos"])
async def upload_video(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
):
    """
    Gateway entry point for video uploads. Validates input and forwards to Video Upload Service.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload."
        )

    url = f"{gateway_settings.UPLOAD_SERVICE_URL}/api/v1/upload"
    
    # Read file content and stream to upload service
    file_content = await file.read()
    files = {"file": (file.filename, file_content, file.content_type)}
    data = {"title": title} if title else {}

    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            resp = await client.post(url, files=files, data=data)
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                media_type=resp.headers.get("content-type", "application/json"),
            )
        except httpx.RequestError as exc:
            logger.error(f"Upload service unreachable: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Video Upload Service unavailable: {exc}"
            )


# ----------------- VIDEO METADATA -----------------

@router.get("/videos", tags=["Videos"])
async def list_videos():
    """
    List all uploaded videos with their metadata and current processing status.
    """
    url = f"{gateway_settings.METADATA_SERVICE_URL}/api/v1/videos"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Metadata service unavailable: {exc}")


@router.get("/videos/{video_id}", tags=["Videos"])
async def get_video_details(video_id: str):
    """
    Get detailed metadata for a specific video.
    """
    url = f"{gateway_settings.METADATA_SERVICE_URL}/api/v1/videos/{video_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Metadata service unavailable: {exc}")


# ----------------- PROCESSING & STATUS -----------------

@router.get("/videos/{video_id}/status", tags=["Orchestration"])
async def get_video_status(video_id: str):
    """
    Get real-time transcoding job status and progress percentage for a video.
    """
    url = f"{gateway_settings.ORCHESTRATOR_SERVICE_URL}/api/v1/status/{video_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Orchestrator service unavailable: {exc}")


@router.post("/videos/{video_id}/process", status_code=status.HTTP_202_ACCEPTED, tags=["Orchestration"])
async def trigger_video_processing(video_id: str, request: Request):
    """
    Manually trigger or restart asynchronous processing for a video.
    """
    url = f"{gateway_settings.ORCHESTRATOR_SERVICE_URL}/api/v1/process/{video_id}"
    body = await request.body()
    headers = {"content-type": request.headers.get("content-type", "application/json")}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(url, content=body, headers=headers)
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Orchestrator service unavailable: {exc}")


@router.get("/jobs/{job_id}", tags=["Orchestration"])
async def get_job_details(job_id: str):
    """
    Get transcoding job details by job_id.
    """
    url = f"{gateway_settings.ORCHESTRATOR_SERVICE_URL}/api/v1/jobs/{job_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Orchestrator service unavailable: {exc}")


# ----------------- OUTPUTS & THUMBNAILS -----------------

@router.get("/videos/{video_id}/outputs", tags=["Media"])
async def get_video_outputs(video_id: str):
    """
    Get all available transcoded resolutions (360p, 720p, 1080p) and media streaming URLs.
    """
    url = f"{gateway_settings.MEDIA_SERVICE_URL}/api/v1/outputs/{video_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Media service unavailable: {exc}")


@router.get("/videos/{video_id}/thumbnails", tags=["Media"])
async def get_video_thumbnails(video_id: str):
    """
    Get all generated thumbnails for a video.
    """
    url = f"{gateway_settings.THUMBNAIL_SERVICE_URL}/api/v1/thumbnails/{video_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Thumbnail service unavailable: {exc}")


# ----------------- MEDIA STREAMING PROXY -----------------

@router.get("/media/{path:path}", tags=["Media"])
async def proxy_media(path: str, request: Request):
    """
    Proxies media streaming requests (videos & thumbnails) to the Media Delivery Service,
    faithfully preserving HTTP 206 Partial Content and Range headers.
    """
    url = f"{gateway_settings.MEDIA_SERVICE_URL}/media/{path}"
    
    # Forward relevant request headers like Range
    forward_headers = {}
    if "range" in request.headers:
        forward_headers["range"] = request.headers["range"]

    client = httpx.AsyncClient(timeout=300.0)
    try:
        req = client.build_request("GET", url, headers=forward_headers)
        resp = await client.send(req, stream=True)

        async def body_stream():
            try:
                async for chunk in resp.aiter_bytes():
                    yield chunk
            finally:
                await resp.aclose()
                await client.aclose()

        response_headers = {
            k: v for k, v in resp.headers.items()
            if k.lower() in ("content-range", "accept-ranges", "content-length", "content-type")
        }

        return StreamingResponse(
            body_stream(),
            status_code=resp.status_code,
            headers=response_headers,
            media_type=resp.headers.get("content-type", "application/octet-stream"),
        )
    except httpx.RequestError as exc:
        await client.aclose()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Media streaming error: {exc}")


# ----------------- SYSTEM HEALTH OVERVIEW -----------------

@router.get("/system/health", tags=["System"])
async def check_all_services_health():
    """
    Checks the health of all microservices in the distributed platform.
    """
    services = {
        "upload_service": f"{gateway_settings.UPLOAD_SERVICE_URL}/health",
        "metadata_service": f"{gateway_settings.METADATA_SERVICE_URL}/health",
        "orchestrator_service": f"{gateway_settings.ORCHESTRATOR_SERVICE_URL}/health",
        "worker_service": f"{gateway_settings.TRANSCODING_SERVICE_URL}/health",
        "thumbnail_service": f"{gateway_settings.THUMBNAIL_SERVICE_URL}/health",
        "media_service": f"{gateway_settings.MEDIA_SERVICE_URL}/health",
    }

    results = {}
    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, url in services.items():
            try:
                res = await client.get(url)
                results[name] = {"status": "UP" if res.status_code == 200 else "DEGRADED", "code": res.status_code}
            except Exception as e:
                results[name] = {"status": "DOWN", "error": str(e)}

    return {
        "gateway": "UP",
        "microservices": results,
    }
