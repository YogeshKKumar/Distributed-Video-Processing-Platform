import os
from typing import Generator, Tuple, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import StreamingResponse, FileResponse

CHUNK_SIZE = 1024 * 256  # 256 KB chunks

def parse_range_header(range_header: str, file_size: int) -> Tuple[int, int]:
    """
    Parses HTTP 'Range' header: 'bytes=start-end' or 'bytes=start-'
    Returns (start_byte, end_byte).
    """
    try:
        units, range_str = range_header.split("=", 1)
        if units.strip() != "bytes":
            return 0, file_size - 1

        parts = range_str.split("-", 1)
        start_str, end_str = parts[0].strip(), parts[1].strip()

        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1

        if start >= file_size or end >= file_size or start > end:
            raise ValueError("Range out of bounds")

        return start, end
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            detail=f"Requested range not satisfiable for file of size {file_size} bytes."
        )


def file_iterator(file_path: str, start: int, end: int, chunk_size: int = CHUNK_SIZE) -> Generator[bytes, None, None]:
    """
    Generator yielding chunks from start to end byte offsets.
    """
    with open(file_path, "rb") as f:
        f.seek(start)
        remaining = (end - start) + 1
        while remaining > 0:
            read_size = min(chunk_size, remaining)
            data = f.read(read_size)
            if not data:
                break
            remaining -= len(data)
            yield data


def stream_video_file(file_path: str, request: Request, content_type: str = "video/mp4") -> StreamingResponse | FileResponse:
    """
    Streams video file handling HTTP 206 Range requests for video seeking.
    """
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range") or request.headers.get("Range")

    if not range_header:
        # Full content response
        return FileResponse(
            path=file_path,
            media_type=content_type,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
            }
        )

    # Partial content response (HTTP 206)
    start, end = parse_range_header(range_header, file_size)
    content_length = (end - start) + 1

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": content_type,
    }

    return StreamingResponse(
        file_iterator(file_path, start, end),
        status_code=status.HTTP_206_PARTIAL_CONTENT,
        headers=headers,
        media_type=content_type,
    )
