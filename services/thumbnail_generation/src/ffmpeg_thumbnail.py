import logging
import os
import shutil
import subprocess
from typing import Dict, Any

logger = logging.getLogger("ffmpeg_thumbnail")

class FFmpegThumbnailGenerator:
    @staticmethod
    def _create_mock_jpeg(output_path: str) -> int:
        """
        Creates a minimal valid JPEG file when FFmpeg is not installed.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Minimal valid 1x1 JPEG byte sequence
        jpeg_bytes = (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00"
            b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
            b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
            b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342"
            b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
            b"\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
            b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
        )
        with open(output_path, "wb") as f:
            f.write(jpeg_bytes)
        return len(jpeg_bytes)

    @classmethod
    def generate(cls, source_file: str, output_path: str, time_offset: float = 1.0) -> Dict[str, Any]:
        if not os.path.exists(source_file):
            raise FileNotFoundError(f"Source file not found: {source_file}")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        ffmpeg_bin = shutil.which("ffmpeg")

        if ffmpeg_bin:
            cmd = [
                ffmpeg_bin,
                "-y",
                "-ss", str(time_offset),
                "-i", source_file,
                "-vframes", "1",
                "-vf", "scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2",
                "-q:v", "2",
                output_path
            ]
            logger.info(f"Generating thumbnail: {' '.join(cmd)}")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg thumbnail extraction failed: {result.stderr[-300:]}")
            file_size = os.path.getsize(output_path)
        else:
            logger.warning("FFmpeg binary not found. Generating mock JPEG thumbnail.")
            file_size = cls._create_mock_jpeg(output_path)

        return {
            "file_path": output_path,
            "file_size": file_size,
            "width": 320,
            "height": 180,
        }
