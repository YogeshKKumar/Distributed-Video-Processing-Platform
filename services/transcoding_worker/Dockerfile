FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install ffmpeg, curl, and build-essential
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY services/transcoding_worker/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --retries 5 -r requirements.txt

# Copy shared library
COPY shared /app/shared

# Copy service source code
COPY services/transcoding_worker /app/services/transcoding_worker
COPY services/transcoding_worker/src /app/src

ENV PYTHONPATH="/app"

EXPOSE 8004

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8004"]
