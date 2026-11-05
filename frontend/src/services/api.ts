import { VideoItem, ProcessingJob, TranscodingOutput, VideoThumbnail, SystemHealthResponse } from '../types';

const API_BASE = ''; // proxied via Vite to Gateway port 8000

export async function fetchVideos(): Promise<VideoItem[]> {
  const res = await fetch(`${API_BASE}/videos`);
  if (!res.ok) throw new Error(`Failed to fetch videos: ${res.statusText}`);
  return res.json();
}

export async function fetchVideoDetails(videoId: string): Promise<VideoItem> {
  const res = await fetch(`${API_BASE}/videos/${videoId}`);
  if (!res.ok) throw new Error(`Failed to fetch video: ${res.statusText}`);
  return res.json();
}

export async function fetchVideoStatus(videoId: string): Promise<ProcessingJob> {
  const res = await fetch(`${API_BASE}/videos/${videoId}/status`);
  if (!res.ok) throw new Error(`Failed to fetch video status: ${res.statusText}`);
  return res.json();
}

export async function fetchJobDetails(jobId: string): Promise<ProcessingJob> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) throw new Error(`Failed to fetch job: ${res.statusText}`);
  return res.json();
}

export async function fetchOutputs(videoId: string): Promise<TranscodingOutput[]> {
  const res = await fetch(`${API_BASE}/videos/${videoId}/outputs`);
  if (!res.ok) throw new Error(`Failed to fetch outputs: ${res.statusText}`);
  return res.json();
}

export async function fetchThumbnails(videoId: string): Promise<VideoThumbnail[]> {
  const res = await fetch(`${API_BASE}/videos/${videoId}/thumbnails`);
  if (!res.ok) throw new Error(`Failed to fetch thumbnails: ${res.statusText}`);
  return res.json();
}

export async function triggerProcessing(videoId: string, resolutions?: string[]): Promise<ProcessingJob> {
  const res = await fetch(`${API_BASE}/videos/${videoId}/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resolutions }),
  });
  if (!res.ok) throw new Error(`Failed to trigger processing: ${res.statusText}`);
  return res.json();
}

export function uploadVideo(
  file: File,
  title: string,
  onProgress?: (percent: number) => void
): Promise<{ video_id: string; title: string }> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);
    if (title.trim()) {
      formData.append('title', title.trim());
    }

    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        const percent = Math.round((event.loaded / event.total) * 100);
        onProgress(percent);
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch {
          resolve({ video_id: '', title: '' });
        }
      } else {
        let errorMsg = `Upload failed (${xhr.status})`;
        try {
          const err = JSON.parse(xhr.responseText);
          if (err.detail) errorMsg = err.detail;
        } catch {}
        reject(new Error(errorMsg));
      }
    });

    xhr.addEventListener('error', () => {
      reject(new Error('Network error during upload'));
    });

    xhr.open('POST', `${API_BASE}/videos/upload`);
    xhr.send(formData);
  });
}

export async function fetchSystemHealth(): Promise<SystemHealthResponse> {
  const res = await fetch(`${API_BASE}/system/health`);
  if (!res.ok) throw new Error('Failed to fetch system health');
  return res.json();
}
