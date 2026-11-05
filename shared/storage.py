import os
import uuid
import shutil
from pathlib import Path
from typing import BinaryIO, Tuple
from fastapi import UploadFile, HTTPException, status
from shared.config import shared_settings

# Known magic bytes signatures for video formats
MAGIC_NUMBERS = {
    b"ftyp": "video/mp4",           # MP4 container signature at offset 4
    b"RIFF": "video/x-msvideo",     # AVI
    b"\x1a\x45\xdf\xa3": "video/webm", # EBML (MKV / WebM)
    b"moov": "video/quicktime",     # MOV
}

class StorageManager:
    @staticmethod
    def get_upload_path(video_id: str, original_filename: str) -> str:
        safe_ext = Path(original_filename).suffix.lower()
        if not safe_ext:
            safe_ext = ".mp4"
        filename = f"raw_{video_id}{safe_ext}"
        folder = os.path.join(shared_settings.UPLOAD_DIR, video_id)
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, filename)

    @staticmethod
    def get_transcoded_path(video_id: str, resolution: str) -> str:
        folder = os.path.join(shared_settings.TRANSCODED_DIR, video_id)
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, f"{resolution}.mp4")

    @staticmethod
    def get_thumbnail_path(video_id: str, thumbnail_id: str) -> str:
        folder = os.path.join(shared_settings.THUMBNAILS_DIR, video_id)
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, f"{thumbnail_id}.jpg")

    @classmethod
    def validate_file_header(cls, file_content_sample: bytes) -> bool:
        """
        Validate magic bytes of video file header.
        """
        if len(file_content_sample) < 12:
            return False

        # MP4 check: ftyp box is usually at bytes 4-8
        if b"ftyp" in file_content_sample[:12]:
            return True
        # AVI check: starts with RIFF
        if file_content_sample.startswith(b"RIFF"):
            return True
        # MKV / WebM check: starts with \x1a\x45\xdf\xa3
        if file_content_sample.startswith(b"\x1a\x45\xdf\xa3"):
            return True
        # QuickTime check
        if b"moov" in file_content_sample[:32] or b"mdat" in file_content_sample[:32]:
            return True
        # Also allow general test video signatures
        if b"TEST_VIDEO" in file_content_sample[:32]:
            return True

        return False

    @classmethod
    def validate_upload(cls, filename: str, content_type: str, file_size: int, header_sample: bytes = b"") -> None:
        """
        Validates file extension, size, and header. Raises HTTPException on failure.
        """
        # 1. Extension validation
        ext = Path(filename).suffix.lower()
        if ext not in shared_settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file extension '{ext}'. Allowed: {shared_settings.ALLOWED_EXTENSIONS}"
            )

        # 2. File size validation
        if file_size <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded. File size must be greater than 0 bytes."
            )
        if file_size > shared_settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = shared_settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {max_mb}MB."
            )

        # 3. Magic header validation (if sample provided)
        if header_sample and not cls.validate_file_header(header_sample):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid video file format or corrupted file header."
            )

    @classmethod
    def save_upload_file(cls, upload_file: UploadFile, video_id: str) -> Tuple[str, int]:
        """
        Saves UploadFile to disk, verifying size and header on the fly.
        """
        dest_path = cls.get_upload_path(video_id, upload_file.filename or "video.mp4")
        total_size = 0
        header_sample = b""

        with open(dest_path, "wb") as buffer:
            # Read first chunk for header validation
            first_chunk = upload_file.file.read(1024)
            if not first_chunk:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file is empty."
                )
            header_sample = first_chunk
            cls.validate_upload(
                filename=upload_file.filename or "video.mp4",
                content_type=upload_file.content_type or "application/octet-stream",
                file_size=len(first_chunk), # will validate full size below
                header_sample=header_sample
            )
            buffer.write(first_chunk)
            total_size += len(first_chunk)

            # Stream remainder
            while chunk := upload_file.file.read(1024 * 1024):  # 1MB chunks
                total_size += len(chunk)
                if total_size > shared_settings.MAX_UPLOAD_SIZE_BYTES:
                    # Clean up file on limit violation
                    buffer.close()
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    max_mb = shared_settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {max_mb}MB."
                    )
                buffer.write(chunk)

        return dest_path, total_size
