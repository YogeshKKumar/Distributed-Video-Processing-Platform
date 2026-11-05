export type ProcessingStatus = 'PENDING' | 'PROCESSING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'RETRYING' | 'UNPROCESSED';

export interface VideoItem {
  id: string;
  video_id: string;
  title: string;
  format: string;
  duration_seconds: number;
  width: number;
  height: number;
  bitrate: number;
  file_size: number;
  processing_status: ProcessingStatus;
  created_at: string;
  updated_at?: string;
}

export interface ProcessingJob {
  id: string;
  video_id: string;
  status: ProcessingStatus;
  target_resolutions: string[];
  completed_resolutions: string[];
  thumbnail_status: 'PENDING' | 'COMPLETED' | 'FAILED' | 'NONE';
  progress_percent: number;
  retry_count: number;
  max_retries: number;
  error_message?: string | null;
  created_at?: string;
}

export interface TranscodingOutput {
  video_id: string;
  resolution: string;
  format: string;
  file_size: number;
  media_url: string;
}

export interface VideoThumbnail {
  id: string;
  video_id: string;
  file_path: string;
  time_offset_seconds: number;
  width: number;
  height: number;
  status: string;
}

export interface ServiceHealth {
  status: 'UP' | 'DOWN' | 'DEGRADED';
  code?: number;
  error?: string;
}

export interface SystemHealthResponse {
  gateway: string;
  microservices: Record<string, ServiceHealth>;
}
