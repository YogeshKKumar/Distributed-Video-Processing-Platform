import os
import tempfile
import pytest
from services.transcoding_worker.src.ffmpeg_transcoder import FFmpegTranscoder
from shared.config import ResolutionConfig

def test_resolution_presets_validity():
    for res_name, config in ResolutionConfig.RESOLUTIONS.items():
        assert "width" in config
        assert "height" in config
        assert "video_bitrate" in config
        assert "audio_bitrate" in config
        assert "crf" in config
        assert "preset" in config
        assert config["width"] > 0
        assert config["height"] > 0


def test_mock_video_generator():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "test_360p.mp4")
        file_size = FFmpegTranscoder._create_mock_video_file(output_file, "360p")

        assert os.path.exists(output_file)
        assert file_size > 0
        with open(output_file, "rb") as f:
            header = f.read(32)
            assert b"ftyp" in header


def test_transcode_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        source_file = os.path.join(tmpdir, "source.mp4")
        FFmpegTranscoder._create_mock_video_file(source_file, "raw")

        output_file = os.path.join(tmpdir, "out_720p.mp4")
        result = FFmpegTranscoder.transcode(source_file, output_file, "720p")

        assert os.path.exists(result["file_path"])
        assert result["height"] == 720
        assert result["width"] == 1280
        assert result["file_size"] > 0
        assert "duration_seconds" in result
        assert "bitrate" in result


def test_transcode_nonexistent_source_raises_error():
    with pytest.raises(FileNotFoundError):
        FFmpegTranscoder.transcode("/non/existent/video.mp4", "/tmp/out.mp4", "360p")


def test_transcode_unknown_resolution_raises_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        source_file = os.path.join(tmpdir, "source.mp4")
        FFmpegTranscoder._create_mock_video_file(source_file, "raw")
        with pytest.raises(ValueError):
            FFmpegTranscoder.transcode(source_file, os.path.join(tmpdir, "out.mp4"), "4000k_invalid")
