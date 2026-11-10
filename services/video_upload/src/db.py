import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
try:
    from .config import upload_settings
    from .models import Base
except (ImportError, ValueError):
    try:
        from src.config import upload_settings
        from src.models import Base
    except (ImportError, ValueError):
        from services.video_upload.src.config import upload_settings
        from services.video_upload.src.models import Base

# Set connect_args for SQLite if used
connect_args = {"check_same_thread": False, "timeout": 20} if "sqlite" in upload_settings.DATABASE_URL else {}

engine = create_engine(
    upload_settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
