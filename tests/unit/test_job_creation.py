import uuid
from services.transcoding_orchestrator.src.models import ProcessingJob

def test_job_progress_calculation():
    job = ProcessingJob(
        video_id=str(uuid.uuid4()),
        status="IN_PROGRESS",
    )
    job.set_target_resolutions_list(["360p", "720p", "1080p"])
    job.set_completed_resolutions_list([])
    job.thumbnail_status = "PENDING"

    # Total 4 steps: 3 resolutions + 1 thumbnail
    # 0 steps completed -> 0%
    assert job.calculate_progress_percent() == 0

    # 1 resolution completed -> 1/4 = 25%
    job.set_completed_resolutions_list(["360p"])
    assert job.calculate_progress_percent() == 25

    # 2 resolutions completed -> 2/4 = 50%
    job.set_completed_resolutions_list(["360p", "720p"])
    assert job.calculate_progress_percent() == 50

    # 3 resolutions completed, thumbnail pending -> 3/4 = 75%
    job.set_completed_resolutions_list(["360p", "720p", "1080p"])
    assert job.calculate_progress_percent() == 75

    # All completed -> 100%
    job.thumbnail_status = "COMPLETED"
    job.status = "COMPLETED"
    assert job.calculate_progress_percent() == 100


def test_job_target_resolutions_serialization():
    job = ProcessingJob(video_id=str(uuid.uuid4()))
    resolutions = ["360p", "480p", "720p", "1080p"]
    job.set_target_resolutions_list(resolutions)

    assert job.get_target_resolutions_list() == resolutions
    data = job.to_dict()
    assert data["target_resolutions"] == resolutions
    assert data["retry_count"] == 0
    assert data["max_retries"] == 3


def test_job_retry_limit():
    job = ProcessingJob(
        video_id=str(uuid.uuid4()),
        max_retries=3,
        retry_count=0,
    )
    assert job.retry_count < job.max_retries

    job.retry_count = 3
    assert job.retry_count >= job.max_retries
