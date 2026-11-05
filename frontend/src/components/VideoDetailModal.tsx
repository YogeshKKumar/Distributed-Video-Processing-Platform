import React, { useEffect, useState } from 'react';
import { X, Film, Info, Image as ImageIcon, RefreshCw } from 'lucide-react';
import { VideoItem, ProcessingJob, TranscodingOutput, VideoThumbnail } from '../types';
import { fetchVideoStatus, fetchOutputs, fetchThumbnails } from '../services/api';
import { VideoPlayer } from './VideoPlayer';
import { JobTracker } from './JobTracker';

interface VideoDetailModalProps {
  video: VideoItem;
  isOpen: boolean;
  onClose: () => void;
  onVideoUpdated: () => void;
}

export const VideoDetailModal: React.FC<VideoDetailModalProps> = ({
  video,
  isOpen,
  onClose,
  onVideoUpdated,
}) => {
  const [job, setJob] = useState<ProcessingJob | null>(null);
  const [outputs, setOutputs] = useState<TranscodingOutput[]>([]);
  const [thumbnails, setThumbnails] = useState<VideoThumbnail[]>([]);
  const [loading, setLoading] = useState(false);

  const loadDetails = async () => {
    setLoading(true);
    try {
      const [jobData, outputsData, thumbsData] = await Promise.all([
        fetchVideoStatus(video.video_id).catch(() => null),
        fetchOutputs(video.video_id).catch(() => []),
        fetchThumbnails(video.video_id).catch(() => []),
      ]);
      setJob(jobData);
      setOutputs(outputsData);
      setThumbnails(thumbsData);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadDetails();
      // Auto poll if processing
      const interval = setInterval(() => {
        if (job && (job.status === 'IN_PROGRESS' || job.status === 'PROCESSING' || job.status === 'RETRYING')) {
          loadDetails();
          onVideoUpdated();
        }
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [isOpen, video.video_id, job?.status]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-800/40 shrink-0">
          <div className="flex items-center space-x-2.5 truncate">
            <Film className="w-5 h-5 text-sky-400 shrink-0" />
            <h3 className="font-semibold text-white text-base truncate">{video.title}</h3>
          </div>
          <div className="flex items-center space-x-2 shrink-0">
            <button
              onClick={loadDetails}
              disabled={loading}
              className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition"
              title="Refresh status"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-sky-400' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Video Player */}
          <VideoPlayer videoId={video.video_id} outputs={outputs} title={video.title} />

          {/* Job Tracker */}
          <JobTracker job={job} videoId={video.video_id} onRefreshJob={loadDetails} />

          {/* Technical Metadata & Thumbnails Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Metadata Card */}
            <div className="bg-slate-800/30 border border-slate-800 rounded-xl p-4 space-y-3">
              <h5 className="font-semibold text-white text-xs flex items-center gap-2 uppercase tracking-wider text-slate-400">
                <Info className="w-4 h-4 text-sky-400" />
                Technical Metadata
              </h5>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80">
                  <span className="text-slate-500 block">Resolution:</span>
                  <span className="font-medium text-slate-200">{video.width} x {video.height}</span>
                </div>
                <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80">
                  <span className="text-slate-500 block">Duration:</span>
                  <span className="font-medium text-slate-200">{video.duration_seconds?.toFixed(1)}s</span>
                </div>
                <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80">
                  <span className="text-slate-500 block">File Size:</span>
                  <span className="font-medium text-slate-200">{(video.file_size / (1024 * 1024)).toFixed(2)} MB</span>
                </div>
                <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80">
                  <span className="text-slate-500 block">Format:</span>
                  <span className="font-medium text-slate-200 uppercase">{video.format}</span>
                </div>
              </div>
            </div>

            {/* Thumbnails Gallery Card */}
            <div className="bg-slate-800/30 border border-slate-800 rounded-xl p-4 space-y-3">
              <h5 className="font-semibold text-white text-xs flex items-center gap-2 uppercase tracking-wider text-slate-400">
                <ImageIcon className="w-4 h-4 text-sky-400" />
                Generated Preview Thumbnails
              </h5>

              {thumbnails.length > 0 ? (
                <div className="grid grid-cols-2 gap-2">
                  {thumbnails.map((t) => (
                    <div key={t.id} className="relative rounded-lg overflow-hidden border border-slate-700 bg-black aspect-video group">
                      <img
                        src={`/media/thumbnails/${t.id}`}
                        alt="Thumbnail"
                        className="w-full h-full object-cover"
                      />
                      <span className="absolute bottom-1 right-1 bg-black/70 text-[10px] text-white px-1.5 py-0.5 rounded font-mono">
                        {t.time_offset_seconds}s
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-28 border border-dashed border-slate-800 rounded-lg flex items-center justify-center text-xs text-slate-500">
                  <span>No thumbnail extracted yet</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
