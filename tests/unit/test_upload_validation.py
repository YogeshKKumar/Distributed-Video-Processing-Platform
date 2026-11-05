import pytest
from io import BytesIO
from fastapi import HTTPException
from shared.storage import StorageManager
from shared.config import shared_settings

def test_valid_mp4_upload(upload_client, valid_mp4_bytes):
    file_payload = {"file": ("test_intro.mp4", BytesIO(valid_mp4_bytes), "video/mp4")}
    data = {"title": "Test Intro Video"}
    response = upload_client.post("/api/v1/upload", files=file_payload, data=data)

    assert response.status_code == 201
    res = response.json()
    assert "video_id" in res
    assert res["filename"] == "test_intro.mp4"
    assert res["title"] == "Test Intro Video"
    assert res["status"] == "UPLOADED"
    assert res["file_size"] == len(valid_mp4_bytes)


def test_reject_unsupported_file_extension(upload_client):
    content = b"Not a video, this is plaintext."
    file_payload = {"file": ("document.txt", BytesIO(content), "text/plain")}
    response = upload_client.post("/api/v1/upload", files=file_payload)

    assert response.status_code == 415
    assert "Unsupported file extension" in response.json()["detail"]


def test_reject_executable_file(upload_client):
    content = b"MZ\x90\x00\x03\x00\x00\x00"
    file_payload = {"file": ("malware.exe", BytesIO(content), "application/x-dosexec")}
    response = upload_client.post("/api/v1/upload", files=file_payload)

    assert response.status_code == 415


def test_reject_empty_file(upload_client):
    file_payload = {"file": ("empty.mp4", BytesIO(b""), "video/mp4")}
    response = upload_client.post("/api/v1/upload", files=file_payload)

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_reject_invalid_corrupted_header(upload_client):
    fake_content = b"GARBAGE_HEADER_DATA_NOT_A_REAL_VIDEO" + (b"\x00" * 100)
    file_payload = {"file": ("corrupt.mp4", BytesIO(fake_content), "video/mp4")}
    response = upload_client.post("/api/v1/upload", files=file_payload)

    assert response.status_code == 400
    assert "Invalid video file format" in response.json()["detail"]


def test_storage_manager_size_limit_validation():
    max_size = shared_settings.MAX_UPLOAD_SIZE_BYTES
    # Test file that exceeds max size
    oversized = max_size + 1024

    with pytest.raises(HTTPException) as exc_info:
        StorageManager.validate_upload(
            filename="large.mp4",
            content_type="video/mp4",
            file_size=oversized,
            header_sample=b"\x00\x00\x00\x20ftypisom"
        )
    assert exc_info.value.status_code == 413
    assert "exceeds maximum allowed size" in exc_info.value.detail


def test_supported_extensions_validation():
    valid_exts = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    for ext in valid_exts:
        # Should not raise exception
        StorageManager.validate_upload(
            filename=f"sample{ext}",
            content_type="video/mp4",
            file_size=1024,
            header_sample=b"\x00\x00\x00\x20ftypisom"
        )
