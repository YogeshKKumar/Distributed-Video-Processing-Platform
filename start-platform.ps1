# Start script for Distributed Video Processing Platform
param (
    [switch]$Local = $false,
    [switch]$Build = $false
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Distributed Video Processing Platform Startup           " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if ($Local) {
    Write-Host "Starting in Standalone / Development Mode (FastAPI + In-Memory Broker)..." -ForegroundColor Yellow
    Write-Host "Please start services in separate terminals or use background jobs:"
    Write-Host "  1. python -m uvicorn services.api_gateway.src.main:app --port 8000 --reload"
    Write-Host "  2. python -m uvicorn services.video_upload.src.main:app --port 8001"
    Write-Host "  3. python -m uvicorn services.video_metadata.src.main:app --port 8002"
    Write-Host "  4. python -m uvicorn services.transcoding_orchestrator.src.main:app --port 8003"
    Write-Host "  5. python -m uvicorn services.transcoding_worker.src.main:app --port 8004"
    Write-Host "  6. python -m uvicorn services.thumbnail_generation.src.main:app --port 8005"
    Write-Host "  7. python -m uvicorn services.media_delivery.src.main:app --port 8006"
    Write-Host "  8. cd frontend; npm run dev"
} else {
    Write-Host "Starting with Docker Compose..." -ForegroundColor Green
    if ($Build) {
        docker compose up -d --build
    } else {
        docker compose up -d
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nPlatform started successfully!" -ForegroundColor Green
        Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
        Write-Host "  React Dashboard:         http://localhost:3001" -ForegroundColor Yellow
        Write-Host "  API Gateway Docs:        http://localhost:8088/docs" -ForegroundColor Yellow
        Write-Host "  RabbitMQ Management:     http://localhost:15673 (guest / guest)" -ForegroundColor Yellow
        Write-Host "  System Health Check:     http://localhost:8088/system/health" -ForegroundColor Yellow
        Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
    } else {
        Write-Host "`nDocker Compose failed. Ensure Docker Desktop is running." -ForegroundColor Red
        Write-Host "To run standalone without Docker, use: .\start-platform.ps1 -Local" -ForegroundColor Yellow
    }
}
