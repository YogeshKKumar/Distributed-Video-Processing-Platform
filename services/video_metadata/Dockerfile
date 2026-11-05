FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install ffmpeg & curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY services/video_metadata/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --retries 5 -r requirements.txt

# Copy shared library
COPY shared /app/shared

# Copy service source code
COPY services/video_metadata/src /app/src

EXPOSE 8002

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--por