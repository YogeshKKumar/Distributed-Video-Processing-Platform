# Distributed Video Processing Platform

A production-grade, distributed video processing platform built using independently deployable Python microservices, RabbitMQ, Redis, MySQL 8, FFmpeg, and a React TypeScript dashboard.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.12, TypeScript |
| **Backend Framework** | FastAPI, Uvicorn |
| **ORM & Database** | SQLAlchemy 2.0, MySQL 8.0 (with SQLite fallback for tests) |
| **Message Broker** | RabbitMQ (Topic Exchange, Dead Letter Exchange `video.dlx`) |
| **Cache & Distributed Locks** | Redis 7 |
| **Media Processing** | FFmpeg (H.264, AAC, scale filter, `+faststart`), FFprobe |
| **Frontend UI** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons |
| **Containerization** | Docker, Docker Compose |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX |

---

## 🏗️ Microservices Architecture

| Service | Host Port | Internal Port | Database | Primary Responsibility |
|---|---|---|---|---|
| **API Gateway Service** | `8088` | `8000` | — | Single frontend entrypoint, request validation, proxying, unified CORS |
| **Video Upload Service** | `8001` | `8001` | `upload_db` | Accepts uploads, validates file format/size/magic bytes, emits `video.uploaded` |
| **Video Metadata Service** | `8002` | `8002` | `metadata_db` | Probes dimensions, duration, format, and tracks video status |
| **Transcoding Orchestrator** | `8003` | `8003` | `orchestrator_db` | Schedules jobs, tracks progress, manages retries (max 3), and routes to DLQ |
| **Transcoding Worker** | `8004` | `8004` | `transcoding_db` | FFmpeg multi-resolution encoding (360p, 720p, 1080p), Redis idempotency lock |
| **Thumbnail Generation** | `8005` | `8005` | `thumbnail_db` | FFmpeg snapshot extraction at specified timestamps |
| **Media Delivery Service** | `8006` | `8006` | — | HTTP 206 Partial Content video streaming (seeking) & thumbnail serving |
| **React Dashboard** | `3001` | `80` | — | Modern web UI for uploading, tracking jobs, and streaming videos |

---

## 🚀 Quickstart with Docker Compose

Ensure Docker and Docker Compose are installed and running.

### 1. Clone & Start Containers
```bash
# Clone or navigate to the project directory
cd distributed-video-platform

# Build and start all services
docker compose up --build
```

### 2. Access the Application
- **React Dashboard**: [http://localhost:3001](http://localhost:3001)
- **API Gateway Swagger Docs**: [http://localhost:8088/docs](http://localhost:8088/docs)
- **RabbitMQ Management Dashboard**: [http://localhost:15673](http://localhost:15673) (User: `guest`, Password: `guest`)
- **API Gateway Health Status**: [http://localhost:8088/system/health](http://localhost:8088/system/health)

---

## 💻 Running in Standalone / Development Mode (Outside Docker)

The platform includes an intelligent **In-Memory Message Broker** and **SQLite / Mock Fallback** enabling all services and tests to run on any machine without Docker or MySQL running.

### 1. Backend Setup
```bash
# Install Python dependencies
pip install -r services/video_upload/requirements.txt
pip install -r tests/requirements-test.txt

# Run API Gateway
python -m uvicorn services.api_gateway.src.main:app --port 8000 --reload

# In separate terminals, run downstream services as needed:
python -m uvicorn services.video_upload.src.main:app --port 8001
python -m uvicorn services.video_metadata.src.main:app --port 8002
python -m uvicorn services.transcoding_orchestrator.src.main:app --port 8003
python -m uvicorn services.transcoding_worker.src.main:app --port 8004
python -m uvicorn services.thumbnail_generation.src.main:app --port 8005
python -m uvicorn services.media_delivery.src.main:app --port 8006
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Dashboard opens on http://localhost:3000
```

---

## 🧪 Automated Testing Suite

The project includes unit, integration, deduplication, fault tolerance, and end-to-end tests.

```bash
# Run the full automated test suite
python -m pytest -v
```

### Test Coverage Highlights
- `tests/unit/test_upload_validation.py`: Tests permitted formats (`.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`), rejects invalid extensions, rejects corrupt headers, rejects empty 0-byte files, and tests 500MB size limits.
- `tests/unit/test_job_creation.py`: Tests job progress calculation (0%, 25%, 50%, 75%, 100%), target resolutions JSON serialization, and retry bounds.
- `tests/unit/test_ffmpeg_transcoder.py`: Tests resolution presets, aspect ratios, faststart streaming flags, and mock generation.
- `tests/integration/test_service_communication.py`: Tests event choreography across Upload, Metadata, Orchestrator, Worker, and Thumbnail services.
- `tests/integration/test_duplicate_messages.py`: Verifies worker idempotency by delivering duplicate messages and confirming only one transcode output is created.
- `tests/integration/test_worker_failures_retry.py`: Tests worker failure recording, orchestrator retry increments, and Dead Letter Queue (DLQ) routing when exceeding 3 attempts.
- `tests/e2e/test_end_to_end_pipeline.py`: Full end-to-end flow from upload -> metadata probe -> multi-resolution transcode -> thumbnail generation -> HTTP 206 range-based media streaming.

---

## 📡 API Reference

All requests can be executed against the **API Gateway** (`http://localhost:8000`):

### 1. Upload Video
```http
POST /videos/upload
Content-Type: multipart/form-data

file: <binary video file>
title: "My Vacation Video"
```
**Response (201 Created)**:
```json
{
  "video_id": "7f8b9e62-c1a4-4df2-8c88-e56d782992b1",
  "filename": "vacation.mp4",
  "title": "My Vacation Video",
  "file_size": 15420100,
  "content_type": "video/mp4",
  "status": "UPLOADED"
}
```

### 2. List Videos
```http
GET /videos
```
**Response (200 OK)**:
```json
[
  {
    "id": "...",
    "video_id": "7f8b9e62-c1a4-4df2-8c88-e56d782992b1",
    "title": "My Vacation Video",
    "format": "mp4",
    "duration_seconds": 32.5,
    "width": 1920,
    "height": 1080,
    "bitrate": 2500000,
    "file_size": 15420100,
    "processing_status": "COMPLETED"
  }
]
```

### 3. Video Processing Status
```http
GET /videos/{video_id}/status
```
**Response (200 OK)**:
```json
{
  "id": "job-uuid",
  "video_id": "7f8b9e62-c1a4-4df2-8c88-e56d782992b1",
  "status": "COMPLETED",
  "target_resolutions": ["360p", "720p", "1080p"],
  "completed_resolutions": ["360p", "720p", "1080p"],
  "thumbnail_status": "COMPLETED",
  "progress_percent": 100,
  "retry_count": 0,
  "max_retries": 3,
  "error_message": null
}
```

### 4. Trigger / Restart Processing
```http
POST /videos/{video_id}/process
Content-Type: application/json

{
  "resolutions": ["360p", "720p", "1080p"]
}
```
**Response (202 Accepted)**:
```json
{
  "id": "job-uuid",
  "video_id": "7f8b9e62-c1a4-4df2-8c88-e56d782992b1",
  "status": "IN_PROGRESS"
}
```

### 5. Available Outputs
```http
GET /videos/{video_id}/outputs
```
**Response (200 OK)**:
```json
[
  {
    "video_id": "7f8b9e62-c1a4-4df2-8c88-e56d782992b1",
    "resolution": "360p",
    "format": "mp4",
    "file_size": 3201400,
    "media_url": "/media/videos/7f8b9e62-c1a4-4df2-8c88-e56d782992b1/360p"
  },
  {
    "video_id": "7f8b9e62-c1a4-4df2-8c88-e56d782992b1",
    "resolution": "720p",
    "format": "mp4",
    "file_size": 8940120,
    "media_url": "/media/videos/7f8b9e62-c1a4-4df2-8c88-e56d782992b1/720p"
  },
  {
    "video_id": "7f8b9e62-c1a4-4df2-8c88-e56d782992b1",
    "resolution": "1080p",
    "format": "mp4",
    "file_size": 14201900,
    "media_url": "/media/videos/7f8b9e62-c1a4-4df2-8c88-e56d782992b1/1080p"
  }
]
```

### 6. Media Streaming (HTTP 206 Range)
```http
GET /media/videos/{video_id}/{resolution}
Range: bytes=0-1048575
```
**Response (206 Partial Content)**:
```http
Content-Range: bytes 0-1048575/8940120
Accept-Ranges: bytes
Content-Length: 1048576
Content-Type: video/mp4
```

### 7. Preview Thumbnails
```http
GET /videos/{video_id}/thumbnails
GET /media/thumbnails/{thumbnail_id}
GET /media/thumbnails/video/{video_id}
```

---

## 🖥️ React Frontend Features

1. **Drag-and-Drop Uploader**: Client-side format filtering, instant 500MB boundary validation, animated upload progress bar.
2. **Video Explorer**: Searchable and filterable grid of all videos with live status badges (`COMPLETED`, `PROCESSING`, `FAILED`, `PENDING`).
3. **Custom HTML5 Video Player**:
   - Dynamic resolution switcher (360p, 720p, 1080p, original raw).
   - Range-based HTTP 206 seeking support.
   - Smooth resolution switching preserving the current timestamp.
4. **Lifecycle & Job Tracker**:
   - Real-time progress bar (0% - 100%).
   - Step indicator across upload, metadata, each resolution, and thumbnails.
   - Attempt counters, error details, and retry triggers.
5. **System Health Mesh Modal**: Live operational status across all 7 microservices and the gateway.

---

## 🛡️ Reliability & Idempotency Guarantees

- **RabbitMQ DLQ**: Unrecoverable transcode attempts are safely pushed to `video.dlx` after 3 retries, preserving full stack trace and error logs.
- **Idempotent Workers**: Re-delivering the same message is detected via Redis distributed locks and unique database constraints (`video_id`, `resolution`), preventing duplicate CPU-heavy transcode runs.
- **Database Isolation**: No microservice accesses another service's tables directly; each has its own schema in MySQL 8.
