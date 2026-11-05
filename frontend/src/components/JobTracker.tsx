import React, { useState } from 'react';
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  Layers,
  Image as ImageIcon,
  Loader2,
} from 'lucide-react';
import { ProcessingJob } from '../types';
import { triggerProcessing } from '../services/api';

interface JobTrackerProps {
  job: ProcessingJob | null;
  videoId: string;
  onRefreshJob: () => void;
}

export const JobTracker: React.FC<JobTrackerProps> = ({ job, videoId, onRefreshJob }) => {
  const [retrying, setRetrying] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const handleRetry = async () => {
    setRetrying(true);
    setActionError(null);
    try {
      await triggerProcessing(videoId);
      onRefreshJob();
    } catch (err: any) {
      setActionError(err.message || 'Failed to retry processing');
    } finally {
      setRetrying(false);
    }
  };

  if (!job) {
    return (
      <div className="bg-slate-800/30 border border-slate-800 rounded-xl p-4 text-center">
        <p className="text-xs text-slate-400">No active job found for this video.</p>
        <button
          onClick={handleRetry}
          disabled={retrying}
          className="mt-2 text-xs bg-sky-600 hover:bg-sky-500 text-white px-3 py-1.5 rounded-lg transition"
        >
          {retrying ? 'Initiating...' : 'Trigger Processing Job'}
        </button>
      </div>
    );
  }

  const isCompleted = job.status === 'COMPLETED';
  const isFailed = job.status === 'FAILED';
  const isProcessing = job.status === 'IN_PROGRESS' || job.status === 'PROCESSING' || job.status === 'RETRYING';

  return (
    <div className="bg-slate-800/40 border border-slate-800 rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-semibold text-white text-sm flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-sky-400" />
            Transcoding Lifecycle & Job Tracker
          </h4>
          <p className="text-xs text-slate-400">Coordinated by Transcoding Orchestrator via RabbitMQ</p>
        </div>

        <div>
          {isCompleted && (
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="w-3.5 h-3.5" />
              COMPLETED
            </span>
          )}
          {isProcessing && (
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 animate-pulse">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              {job.status}
            </span>
          )}
          {isFailed && (
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-red-500/10 text-red-400 border border-red-500/20">
              <AlertTriangle className="w-3.5 h-3.5" />
              FAILED
            </span>
          )}
        </div>
      </div>

      {actionError && (
        <div className="p-2.5 bg-red-950/40 border border-red-500/40 rounded-lg text-red-300 text-xs">
          {actionError}
        </div>
      )}

      {/* Progress Bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs text-slate-400">
          <span>Overall Workflow Progress</span>
          <span className="font-semibold text-sky-400">{job.progress_percent}%</span>
        </div>
        <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-800">
          <div
            className={`h-2.5 transition-all duration-300 ${
              isCompleted
                ? 'bg-emerald-500'
                : isFailed
                ? 'bg-red-500'
                : 'bg-gradient-to-r from-sky-500 to-indigo-500'
            }`}
            style={{ width: `${job.progress_percent}%` }}
          />
        </div>
      </div>

      {/* Step Breakdown */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
        {['360p', '720p', '1080p'].map((res) => {
          const isDone = job.completed_resolutions?.includes(res);
          return (
            <div
              key={res}
              className={`p-2.5 rounded-lg border text-xs flex items-center justify-between ${
                isDone
                  ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                  : isProcessing
                  ? 'bg-slate-900/60 border-slate-800 text-slate-400'
                  : 'bg-slate-900/40 border-slate-800 text-slate-500'
              }`}
            >
              <div className="flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-slate-400" />
                <span>{res}</span>
              </div>
              {isDone ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <Clock className="w-3.5 h-3.5 text-slate-500" />
              )}
            </div>
          );
        })}

        <div
          className={`p-2.5 rounded-lg border text-xs flex items-center justify-between ${
            job.thumbnail_status === 'COMPLETED'
              ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
              : 'bg-slate-900/60 border-slate-800 text-slate-400'
          }`}
        >
          <div className="flex items-center gap-1.5">
            <ImageIcon className="w-3.5 h-3.5 text-slate-400" />
            <span>Thumbnails</span>
          </div>
          {job.thumbnail_status === 'COMPLETED' ? (
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          ) : (
            <Clock className="w-3.5 h-3.5 text-slate-500" />
          )}
        </div>
      </div>

      {/* Retry & Error Information */}
      {(job.retry_count > 0 || job.error_message || isFailed) && (
        <div className="bg-slate-900/70 border border-slate-800 rounded-lg p-3 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">
              Processing Attempts: <strong className="text-slate-200">{job.retry_count} / {job.max_retries}</strong>
            </span>
            {isFailed && (
              <span className="text-red-400 font-medium">Routed to Dead Letter Queue (DLQ)</span>
            )}
          </div>

          {job.error_message && (
            <div className="p-2 bg-red-950/30 border border-red-500/30 rounded text-red-300 text-xs font-mono break-words">
              {job.error_message}
            </div>
          )}

          <div className="pt-1 flex justify-end">
            <button
              onClick={handleRetry}
              disabled={retrying}
              className="flex items-center space-x-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-sky-400 px-3 py-1.5 rounded-lg border border-slate-700 transition"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${retrying ? 'animate-spin' : ''}`} />
              <span>{retrying ? 'Restarting...' : 'Retry Processing'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
