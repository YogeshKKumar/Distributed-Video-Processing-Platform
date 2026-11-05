from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.video_metadata.src.config import metadata_settings
from services.video_metadata.src.models import Base

connect_args = {"check_same_thread": False, "timeout": 20} if "sqlite" in metadata_settings.DATABASE_URL else {}

engine = create_engine(
    metadata_settings.DATABASE_URL,
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
