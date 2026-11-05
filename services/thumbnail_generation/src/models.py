import datetime
import uuid
from sqlalchemy import Column, String, Float, Integer, BigInteger, Text, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class VideoThumbnail(Base):
    __tablename__ = "video_thumbnails"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String(36), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    time_offset_seconds = Column(Float, nullable=False, default=1.0)
    width = Column(Integer, nullable=False, default=320)
    height = Column(Integer, nullable=False, default=180)
    file_size = Column(BigInteger, nullable=False, default=0)
    status = Column(String(30), nullable=False, default="PENDING")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "video_id": self.video_id,
            "file_path": self.file_path,
            "time_offset_seconds": self.time_offset_seconds,
            "width": self.width,
            "height": self.height,
            "file_size": self.file_size,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
