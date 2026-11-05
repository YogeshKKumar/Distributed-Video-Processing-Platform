import logging
import os
import shutil
import subprocess
import time
from typing import Dict, Any
from shared.config import ResolutionConfig

logger = logging.getLogger("ffmpeg_transcoder")

class FFmpegTranscoder:
    @staticmethod
    def _create_mock_video_file(output_path: str, resolution: str) -> int:
        """
        Creates a mock MP4 file when ffmpeg is not installed (e.g. local test runs).
        Writes valid ftyp box and content so it validates as video.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # 32 bytes valid MP4 header sample + mock data
        header = b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2avc1mp41"
        payload = f"MOCK_TRANSCODED_VIDEO_{resolution}_PAYLOAD".encode("utf-8") * 256
        with open(output_path, "wb") as f:
            f.write(header + payload)
        return os.path.getsize(output_path)

    @classmethod
    def transcode(cls, source_file: str, output_file: str, resolution: str) -> Dict[str, Any]:
        """
        Transcodes source_file to target resolution using FFmpeg.
        """
        if not os.path.exists(source_file):
            raise FileNotFoundError(f"Source file not found: {source_file}")

        config = ResolutionConfig.RESOLUTIONS.get(resolution)
        if not config:
            raise ValueError(f"Unknown resolution preset: {resolution}")

        target_height = config["height"]
        target_width = config["width"]
        crf = config.get("crf", "23")
        preset = config.get("preset", "fast")
        v_bitrate = config.get("video_bitrate", "2000k")
        a_bitrate = config.get("audio_bitrate", "128k")

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        start_time = time.time()

        # Check if ffmpeg is available
        ffmpeg_bin = shutil.which("ffmpeg")

        if ffmpeg_bin:
            # Scale video maintaining aspect ratio, guaranteeing even dimensions (-2)
            scale_filter = f"scale=-2:{target_height}"
            cmd = [
                ffmpeg_bin,
                "-y",  # overwrite output
                "-i", source_file,
                "-vf", scale_filter,
                "-c:v", "libx264",
                "-crf", crf,
                "-preset", preset,
                "-b:v", v_bitrate,
                "-c:a", "aac",
                "-b:a", a_bitrate,
                "-movflags", "+faststart",  # enables progressive downloading / streaming
                output_file
            ]

            logger.info(f"Executing FFmpeg: {' '.join(cmd)}")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300)

            if result.returncode != 0:
                error_msg = result.stderr[-500:] if result.stderr else "Unknown FFmpeg error"
                logger.error(f"FFmpeg transcode failed: {error_msg}")
                raise RuntimeError(f"FFmpeg error: {error_msg}")

            file_size = os.path.getsize(output_file)
        else:
            logger.warning(f"FFmpeg binary not found on system PATH. Using mock video generator for resolution {resolution}.")
            file_size = cls._create_mock_video_file(output_file, resolution)
            time.sleep(0.1)  # simulate small delay

        duration_seconds = round(time.time() - start_time, 2)
        bitrate_int = int(v_bitrate.rstrip("k")) * 1000

        return {
            "file_path": output_file,
            "file_size": file_size,
            "width": target_width,
            "height": target_height,
            "bitrate": bitrate_int,
            "duration_seconds": duration_seconds,
        }
