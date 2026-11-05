import React, { useState } from 'react';
import {
  Film,
  Play,
  Clock,
  HardDrive,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Search,
  Filter,
  Loader2,
} from 'lucide-react';
import { VideoItem, ProcessingStatus } from '../types';
import { triggerProcessing } from '../services/api';

interface VideoListProps {
  videos: VideoItem[];
  onSelectVideo: (video: VideoItem) => void;
  onRefresh: () => void;
}

export const VideoList: React.FC<VideoListProps> = ({ videos, onSelectVideo, onRefresh }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [processingId, setProcessingId] = useState<string | null>(null);

  const handleTriggerProcess = async (e: React.MouseEvent, videoId: string) => {
    e.stopPropagation();
    setProcessingId(videoId);
    try {
      await triggerProcessing(videoId);
      onRefresh();
    } catch (err: any) {
      alert(`Error triggering process: ${err.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  const filteredVideos = videos.filter((video) => {
    const matchesSearch =
      video.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      video.video_id.toLowerCase().includes(searchTerm.toLowerCase());
    if (statusFilter === 'ALL') return matchesSearch;
    return matchesSearch && video.processing_status === statusFilter;
  });

  const getStatusBadge = (status: ProcessingStatus) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" />
            COMPLETED
          </span>
        );
      case 'IN_PROGRESS':
      case 'PROCESSING':
      case 'RETRYING':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 animate-pulse">
            <Loader2 className="w-3 h-3 animate-spin" />
            PROCESSING
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20">
            <AlertTriangle className="w-3 h-3" />
            FAILED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Clock className="w-3 h-3" />
            PENDING
          </span>
        );
    }
  };

  return (
    <div className="space-y-4">
      {/* Search & Filter Header */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search videos by title..."
            className="w-full bg-slate-800/80 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-sky-500 transition"
          />
        </div>

        <div className="flex items-center space-x-1.5 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          <Filter className="w-3.5 h-3.5 text-slate-400 mr-1 hidden sm:inline" />
          {['ALL', 'COMPLETED', 'PROCESSING', 'PENDING', 'FAILED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`text-xs px-2.5 py-1 rounded-md font-medium transition whitespace-nowrap ${
                statusFilter === st
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Videos Grid */}
      {filteredVideos.length === 0 ? (
        <div className="bg-slate-800/20 border border-dashed border-slate-800 rounded-xl p-12 text-center">
          <Film className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-medium text-slate-300">No videos found</h3>
          <p className="text-xs text-slate-500 mt-1">Upload a video or adjust search criteria to see videos.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredVideos.map((video) => (
            <div
              key={video.video_id}
              onClick={() => onSelectVideo(video)}
              className="bg-slate-800/40 hover:bg-slate-800/70 border border-slate-800 hover:border-slate-700 rounded-xl overflow-hidden shadow-lg transition cursor-pointer flex flex-col group"
            >
              {/* Thumbnail Container */}
              <div className="relative aspect-video bg-black flex items-center justify-center overflow-hidden">
                <img
                  src={`/media/thumbnails/video/${video.video_id}`}
                  alt={video.title}
                  onError={(e) => {
                    // Fallback to placeholder if thumbnail is not generated yet
                    (e.target as HTMLImageElement).src =
                      'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180" viewBox="0 0 320 180" fill="%230f172a"><rect width="320" height="180" fill="%231e293b"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="%2364748b" font-family="sans-serif" font-size="12">Thumbnail in progress...</text></svg>';
                  }}
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                />

                <div className="absolute inset-0 bg-black/30 group-hover:bg-black/10 transition flex items-center justify-center">
                  <div className="w-10 h-10 rounded-full bg-sky-600/90 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition shadow-lg transform group-hover:scale-110">
                    <Play className="w-5 h-5 ml-0.5 fill-current" />
                  </div>
                </div>

                <div className="absolute top-2 left-2">
                  {getStatusBadge(video.processing_status)}
                </div>

                {video.duration_seconds > 0 && (
                  <div className="absolute bottom-2 right-2 bg-black/80 text-[10px] text-white px-1.5 py-0.5 rounded font-mono">
                    {Math.floor(video.duration_seconds / 60)}:
                    {Math.floor(video.duration_seconds % 60).toString().padStart(2, '0')}
                  </div>
                )}
              </div>

              {/* Body */}
              <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                <div>
                  <h4 className="font-semibold text-white text-sm line-clamp-1 group-hover:text-sky-400 transition">
                    {video.title}
                  </h4>
                  <p className="text-[11px] text-slate-500 font-mono mt-0.5">ID: {video.video_id.substring(0, 8)}...</p>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-2.5">
                  <div className="flex items-center space-x-1">
                    <HardDrive className="w-3.5 h-3.5 text-slate-500" />
                    <span>{(video.file_size / (1024 * 1024)).toFixed(1)} MB</span>
                  </div>

                  <div className="flex items-center space-x-2">
                    {video.processing_status !== 'COMPLETED' && (
                      <button
                        onClick={(e) => handleTriggerProcess(e, video.video_id)}
                        disabled={processingId === video.video_id}
                        className="text-[11px] text-sky-400 hover:text-sky-300 bg-sky-950/40 hover:bg-sky-900/40 px-2 py-0.5 rounded border border-sky-500/30 transition flex items-center gap-1"
                        title="Trigger / Re-run Transcoding Job"
                      >
                        <RotateCcw className={`w-3 h-3 ${processingId === video.video_id ? 'animate-spin' : ''}`} />
                        <span>Process</span>
                      </button>
                    )}

                    <span className="text-[11px] font-medium text-slate-400 uppercase bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                      {video.format}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
