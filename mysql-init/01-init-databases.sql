-- Initialize separate databases for each microservice boundary
CREATE DATABASE IF NOT EXISTS upload_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS metadata_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS orchestrator_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS transcoding_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS thumbnail_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Grant permissions to default video_user
CREATE USER IF NOT EXISTS 'video_user'@'%' IDENTIFIED BY 'video_pass';
GRANT ALL PRIVILEGES ON upload_db.* TO 'video_user'@'%';
GRANT ALL PRIVILEGES ON metadata_db.* TO 'video_user'@'%';
GRANT ALL PRIVILEGES ON orchestrator_db.* TO 'video_user'@'%';
GRANT ALL PRIVILEGES ON transcoding_db.* TO 'video_user'@'%';
GRANT ALL PRIVILEGES ON thumbnail_db.* TO 'video_user'@'%';
FLUSH PRIVILEGES;

-- 1. Video Upload Service Schema (videos table)
USE upload_db;
CREATE TABLE IF NOT EXISTS videos (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'UPLOADED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_videos_created (created_at)
) ENGINE=InnoDB;

-- 2. Video Metadata Service Schema (video_metadata table)
USE metadata_db;
CREATE TABLE IF NOT EXISTS video_metadata (
    id VARCHAR(36) PRIMARY KEY,
    video_id VARCHAR(36) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    format VARCHAR(50) NOT NULL,
    duration_seconds FLOAT NOT NULL DEFAULT 0.0,
    width INT NOT NULL DEFAULT 0,
    height INT NOT NULL DEFAULT 0,
    bitrate INT NOT NULL DEFAULT 0,
    file_size BIGINT NOT NULL,
    processing_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_video_metadata_status (processing_status)
) ENGINE=InnoDB;

-- 3. Transcoding Orchestrator Service Schema (processing_jobs table)
USE orchestrator_db;
CREATE TABLE IF NOT EXISTS processing_jobs (
    id VARCHAR(36) PRIMARY KEY,
    video_id VARCHAR(36) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    target_resolutions TEXT NOT NULL,
    completed_resolutions TEXT,
    thumbnail_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    retry_count INT NOT NULL DEFAULT 0,
    max_retries INT NOT NULL DEFAULT 3,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_processing_jobs_video (video_id),
    INDEX idx_processing_jobs_status (status)
) ENGINE=InnoDB;

-- 4. Transcoding Worker Service Schema (processing_attempts & transcoding_outputs tables)
USE transcoding_db;
CREATE TABLE IF NOT EXISTS processing_attempts (
    id VARCHAR(36) PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL,
    video_id VARCHAR(36) NOT NULL,
    resolution VARCHAR(20) NOT NULL,
    attempt_number INT NOT NULL,
    status VARCHAR(30) NOT NULL,
    duration_seconds FLOAT,
    error_details TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    INDEX idx_attempts_job (job_id),
    INDEX idx_attempts_video (video_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS transcoding_outputs (
    id VARCHAR(36) PRIMARY KEY,
    video_id VARCHAR(36) NOT NULL,
    job_id VARCHAR(36) NOT NULL,
    resolution VARCHAR(20) NOT NULL,
    width INT NOT NULL,
    height INT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    bitrate INT NOT NULL,
    format VARCHAR(20) NOT NULL DEFAULT 'mp4',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_video_resolution (video_id, resolution),
    INDEX idx_outputs_video (video_id),
    INDEX idx_outputs_job (job_id)
) ENGINE=InnoDB;

-- 5. Thumbnail Generation Service Schema (video_thumbnails table)
USE thumbnail_db;
CREATE TABLE IF NOT EXISTS video_thumbnails (
    id VARCHAR(36) PRIMARY KEY,
    video_id VARCHAR(36) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    time_offset_seconds FLOAT NOT NULL DEFAULT 1.0,
    width INT NOT NULL DEFAULT 320,
    height INT NOT NULL DEFAULT 180,
    file_size BIGINT NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_thumbnails_video (video_id)
) ENGINE=InnoDB;
