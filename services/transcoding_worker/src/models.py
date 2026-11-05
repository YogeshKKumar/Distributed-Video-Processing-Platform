import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, BigInteger, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ProcessingAttempt(Base):
    __tablename__ = "processing_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), nullable=False, index=True)
    video_id = Column(String(36), nullable=False, index=True)
    resolution = Column(String(20), nullable=False)
    attempt_number = Column(Integer, nullable=False, default=1)
    status = Column(String(30), nullable=False)  # STARTED, SUCCESS, FAILED
    duration_seconds = Column(Float, nullable=True)
    error_details = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "video_id": self.video_id,
            "resolution": self.resolution,
            "attempt_number": self.attempt_number,
            "status": self.status,
            "duration_seconds": self.duration_seconds,
            "error_details": self.error_details,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class TranscodingOutput(Base):
    __tablename__ = "transcoding_outputs"
    __table_args__ = (
        UniqueConstraint("video_id", "resolution", name="uq_video_resolution"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String(36), nullable=False, index=True)
    job_id = Column(String(36), nullable=False, index=True)
    resolution = Column(String(20), nullable=False)  # 360p, 720p, 1080p
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    bitrate = Column(Integer, nullable=False)
    format = Column(String(20), nullable=False, default="mp4")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "video_id": self.video_id,
            "job_id": self.job_id,
            "resolution": self.resolution,
            "width": self.width,
            "height": self.height,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "bitrate": self.bitrate,
            "format": self.format,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
