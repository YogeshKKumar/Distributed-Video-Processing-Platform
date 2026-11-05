import os
import sys
import shutil
import tempfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root to sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Configure environment for tests
TEST_DATA_DIR = tempfile.mkdtemp(prefix="video_test_")
os.environ["DATA_DIR"] = TEST_DATA_DIR
os.environ["USE_IN_MEMORY_BROKER"] = "true"
os.environ["UPLOAD_DATABASE_URL"] = f"sqlite:///{os.path.join(TEST_DATA_DIR, 'test_upload.db')}"
os.environ["METADATA_DATABASE_URL"] = f"sqlite:///{os.path.join(TEST_DATA_DIR, 'test_metadata.db')}"
os.environ["ORCHESTRATOR_DATABASE_URL"] = f"sqlite:///{os.path.join(TEST_DATA_DIR, 'test_orchestrator.db')}"
os.environ["TRANSCODING_DATABASE_URL"] = f"sqlite:///{os.path.join(TEST_DATA_DIR, 'test_transcoding.db')}"
os.environ["THUMBNAIL_DATABASE_URL"] = f"sqlite:///{os.path.join(TEST_DATA_DIR, 'test_thumbnail.db')}"

from shared.config import shared_settings
from shared.messaging import message_broker

# Initialize databases
from services.video_upload.src.db import init_db as init_upload_db
from services.video_metadata.src.db import init_db as init_metadata_db
from services.transcoding_orchestrator.src.db import init_db as init_orchestrator_db
from services.transcoding_worker.src.db import init_db as init_worker_db
from services.thumbnail_generation.src.db import init_db as init_thumbnail_db

from services.video_upload.src.main import app as upload_app
from services.video_metadata.src.main import app as metadata_app
from services.transcoding_orchestrator.src.main import app as orchestrator_app
from services.transcoding_worker.src.main import app as worker_app
from services.thumbnail_generation.src.main import app as thumbnail_app
from services.media_delivery.src.main import app as media_app
from services.api_gateway.src.main import app as gateway_app


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    shared_settings.DATA_DIR = TEST_DATA_DIR
    shared_settings.UPLOAD_DIR = os.path.join(TEST_DATA_DIR, "uploads")
    shared_settings.TRANSCODED_DIR = os.path.join(TEST_DATA_DIR, "transcoded")
    shared_settings.THUMBNAILS_DIR = os.path.join(TEST_DATA_DIR, "thumbnails")
    shared_settings.DBS_DIR = os.path.join(TEST_DATA_DIR, "dbs")

    for p in [shared_settings.UPLOAD_DIR, shared_settings.TRANSCODED_DIR, shared_settings.THUMBNAILS_DIR, shared_settings.DBS_DIR]:
        os.makedirs(p, exist_ok=True)

    init_upload_db()
    init_metadata_db()
    init_orchestrator_db()
    init_worker_db()
    init_thumbnail_db()

    yield

    shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def reset_message_broker():
    """
    Clears message broker history and subscribers between tests.
    """
    message_broker.in_memory.clear()
    # Re-wire subscriptions for active test services
    from services.video_metadata.src.routes import handle_video_uploaded, handle_job_status_updated
    from services.transcoding_orchestrator.src.orchestrator import (
        handle_transcode_completed,
        handle_transcode_failed,
        handle_thumbnail_completed,
        handle_thumbnail_failed,
    )
    from services.transcoding_worker.src.worker import process_transcode_task
    from services.thumbnail_generation.src.worker import process_thumbnail_task

    message_broker.subscribe("video.uploaded", handle_video_uploaded)
    message_broker.subscribe("event.job.status_updated", handle_job_status_updated)
    message_broker.subscribe("event.transcode.completed", handle_transcode_completed)
    message_broker.subscribe("event.transcode.failed", handle_transcode_failed)
    message_broker.subscribe("event.thumbnail.completed", handle_thumbnail_completed)
    message_broker.subscribe("event.thumbnail.failed", handle_thumbnail_failed)
    message_broker.subscribe("job.transcode", process_transcode_task)
    message_broker.subscribe("job.thumbnail", process_thumbnail_task)


@pytest.fixture
def valid_mp4_bytes() -> bytes:
    """
    Returns valid MP4 container sample with 'ftyp' box.
    """
    header = b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2avc1mp41"
    payload = b"\x00" * 4096
    return header + payload


@pytest.fixture
def upload_client():
    return TestClient(upload_app)


@pytest.fixture
def metadata_client():
    return TestClient(metadata_app)


@pytest.fixture
def orchestrator_client():
    return TestClient(orchestrator_app)


@pytest.fixture
def worker_client():
    return TestClient(worker_app)


@pytest.fixture
def thumbnail_client():
    return TestClient(thumbnail_app)


@pytest.fixture
def media_client():
    return TestClient(media_app)


@pytest.fixture
def gateway_client():
    return TestClient(gateway_app)
