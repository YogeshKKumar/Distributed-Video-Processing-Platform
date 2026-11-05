import React, { useState, useRef, useEffect } from 'react';
import { Settings2, Download, AlertCircle } from 'lucide-react';
import { TranscodingOutput } from '../types';

interface VideoPlayerProps {
  videoId: string;
  outputs: TranscodingOutput[];
  title: string;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({ videoId, outputs, title }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [selectedResolution, setSelectedResolution] = useState<string>('720p');

  // Available options: outputs + raw fallback
  const availableRes = outputs.map((o) => o.resolution);

  useEffect(() => {
    // Default to highest available or 720p or raw
    if (availableRes.includes('1080p')) {
      setSelectedResolution('1080p');
    } else if (availableRes.includes('720p')) {
      setSelectedResolution('720p');
    } else if (availableRes.includes('360p')) {
      setSelectedResolution('360p');
    } else {
      setSelectedResolution('raw');
    }
  }, [outputs]);

  const handleResolutionChange = (newRes: string) => {
    if (videoRef.current) {
      const time = videoRef.current.currentTime;
      const wasPlaying = !videoRef.current.paused;
      setSelectedResolution(newRes);

      // Re-apply playback state after source change
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.currentTime = time;
          if (wasPlaying) videoRef.current.play();
        }
      }, 50);
    }
  };

  const getMediaUrl = () => {
    if (selectedResolution === 'raw') {
      return `/media/raw/${videoId}`;
    }
    return `/media/videos/${videoId}/${selectedResolution}`;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      <div className="relative bg-black aspect-video flex items-center justify-center">
        <video
          ref={videoRef}
          key={selectedResolution}
          src={getMediaUrl()}
          controls
          className="w-full h-full object-contain"
        >
          Your browser does not support HTML5 video streaming.
        </video>

        {outputs.length === 0 && selectedResolution !== 'raw' && (
          <div className="absolute inset-0 bg-black/80 flex flex-col items-center justify-center p-6 text-center">
            <AlertCircle className="w-10 h-10 text-amber-400 mb-2" />
            <p className="text-sm font-medium text-white">Transcoded outputs not ready yet</p>
            <p className="text-xs text-slate-400 mt-1">Transcoding job is still processing in the background.</p>
            <button
              onClick={() => handleResolutionChange('raw')}
              className="mt-3 text-xs bg-slate-800 hover:bg-slate-700 text-sky-400 px-3 py-1.5 rounded-lg border border-slate-700 transition"
            >
              Play Original Raw File
            </button>
          </div>
        )}
      </div>

      <div className="p-4 bg-slate-800/40 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h4 className="font-semibold text-white text-sm truncate max-w-md">{title}</h4>
          <p className="text-xs text-slate-400">Streamed via Media Delivery Service (HTTP 206 Partial Content)</p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1.5 bg-slate-900 border border-slate-700 px-2.5 py-1.5 rounded-lg">
            <Settings2 className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs text-slate-400">Resolution:</span>
            <select
              value={selectedResolution}
              onChange={(e) => handleResolutionChange(e.target.value)}
              className="bg-transparent text-xs font-semibold text-sky-400 focus:outline-none cursor-pointer"
            >
              {outputs.map((out) => (
                <option key={out.resolution} value={out.resolution} className="bg-slate-900 text-white">
                  {out.resolution} ({(out.file_size / (1024 * 1024)).toFixed(1)}MB)
                </option>
              ))}
              <option value="raw" className="bg-slate-900 text-white">
                Original (Raw)
              </option>
            </select>
          </div>

          <a
            href={getMediaUrl()}
            download
            className="flex items-center space-x-1 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-700 transition"
            title="Download video file"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Download</span>
          </a>
        </div>
      </div>
    </div>
  );
};
