import datetime
import uuid
from sqlalchemy import Column, String, BigInteger, Float, Integer, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class VideoMetadata(Base):
    __tablename__ = "video_metadata"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String(36), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    format = Column(String(50), nullable=False)
    duration_seconds = Column(Float, nullable=False, default=0.0)
    width = Column(Integer, nullable=False, default=0)
    height = Column(Integer, nullable=False, default=0)
    bitrate = Column(Integer, nullable=False, default=0)
    file_size = Column(BigInteger, nullable=False)
    processing_status = Column(String(30), nullable=False, default="PENDING")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "video_id": self.video_id,
            "title": self.title,
            "format": self.format,
            "duration_seconds": self.duration_seconds,
            "width": self.width,
            "height": self.height,
            "bitrate": self.bitrate,
            "file_size": self.file_size,
            "processing_status": self.processing_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
