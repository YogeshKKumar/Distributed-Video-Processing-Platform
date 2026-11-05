import datetime
import json
import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String(36), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="PENDING", index=True)
    target_resolutions = Column(Text, nullable=False, default="[]")
    completed_resolutions = Column(Text, nullable=False, default="[]")
    thumbnail_status = Column(String(30), nullable=False, default="PENDING")
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.retry_count is None:
            self.retry_count = 0
        if self.max_retries is None:
            self.max_retries = 3
        if self.status is None:
            self.status = "PENDING"
        if self.thumbnail_status is None:
            self.thumbnail_status = "PENDING"

    def get_target_resolutions_list(self) -> list[str]:
        try:
            return json.loads(self.target_resolutions) if self.target_resolutions else []
        except Exception:
            return []

    def get_completed_resolutions_list(self) -> list[str]:
        try:
            return json.loads(self.completed_resolutions) if self.completed_resolutions else []
        except Exception:
            return []

    def set_target_resolutions_list(self, resolutions: list[str]):
        self.target_resolutions = json.dumps(resolutions)

    def set_completed_resolutions_list(self, resolutions: list[str]):
        self.completed_resolutions = json.dumps(resolutions)

    def calculate_progress_percent(self) -> int:
        targets = self.get_target_resolutions_list()
        completed = self.get_completed_resolutions_list()
        total_steps = len(targets) + 1  # targets + thumbnail
        if total_steps == 0:
            return 100 if self.status == "COMPLETED" else 0

        done_steps = len(completed)
        if self.thumbnail_status == "COMPLETED":
            done_steps += 1

        percent = int((done_steps / total_steps) * 100)
        if self.status == "COMPLETED":
            return 100
        return min(percent, 99)

    def to_dict(self):
        targets = self.get_target_resolutions_list()
        completed = self.get_completed_resolutions_list()
        return {
            "id": self.id,
            "video_id": self.video_id,
            "status": self.status,
            "target_resolutions": targets,
            "completed_resolutions": completed,
            "thumbnail_status": self.thumbnail_status,
            "progress_percent": self.calculate_progress_percent(),
            "retry_count": self.retry_count if self.retry_count is not None else 0,
            "max_retries": self.max_retries if self.max_retries is not None else 3,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
