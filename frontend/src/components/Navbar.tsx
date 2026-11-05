import React from 'react';
import { Video, Activity, RefreshCw, Layers } from 'lucide-react';

interface NavbarProps {
  totalVideos: number;
  onRefresh: () => void;
  onOpenHealth: () => void;
  isRefreshing: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  totalVideos,
  onRefresh,
  onOpenHealth,
  isRefreshing,
}) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-sky-500/20 p-2 rounded-lg border border-sky-500/30 text-sky-400">
            <Video className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              CloudTranscode
              <span className="text-xs px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 font-medium">
                Distributed Microservices
              </span>
            </h1>
            <p className="text-xs text-slate-400">RabbitMQ • FFmpeg • Redis • MySQL</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="hidden sm:flex items-center space-x-2 text-xs text-slate-400 bg-slate-800/60 px-3 py-1.5 rounded-md border border-slate-700/50">
            <Layers className="w-4 h-4 text-sky-400" />
            <span>Total Videos: <strong className="text-white">{totalVideos}</strong></span>
          </div>

          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700/80 px-3 py-1.5 rounded-md border border-slate-700 transition"
            title="Refresh videos"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-sky-400' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={onOpenHealth}
            className="flex items-center space-x-1.5 text-xs text-emerald-400 hover:text-emerald-300 bg-emerald-950/40 hover:bg-emerald-900/40 px-3 py-1.5 rounded-md border border-emerald-500/30 transition"
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Service Mesh</span>
          </button>
        </div>
      </div>
    </header>
  );
};
