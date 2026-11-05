import React, { useEffect, useState, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { VideoUpload } from './components/VideoUpload';
import { VideoList } from './components/VideoList';
import { VideoDetailModal } from './components/VideoDetailModal';
import { HealthStatus } from './components/HealthStatus';
import { fetchVideos } from './services/api';
import { VideoItem } from './types';

export const App: React.FC = () => {
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<VideoItem | null>(null);
  const [isHealthOpen, setIsHealthOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadVideos = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const data = await fetchVideos();
      setVideos(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load videos from API Gateway');
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadVideos();

    // Auto-poll every 4 seconds if any video is currently processing
    const interval = setInterval(() => {
      const hasActive = videos.some(
        (v) =>
          v.processing_status === 'IN_PROGRESS' ||
          v.processing_status === 'PROCESSING' ||
          v.processing_status === 'PENDING' ||
          v.processing_status === 'RETRYING'
      );
      if (hasActive) {
        loadVideos();
      }
    }, 4000);

    return () => clearInterval(interval);
  }, [loadVideos, videos]);

  const handleUploadSuccess = () => {
    loadVideos();
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      <Navbar
        totalVideos={videos.length}
        onRefresh={loadVideos}
        onOpenHealth={() => setIsHealthOpen(true)}
        isRefreshing={isRefreshing}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {error && (
          <div className="p-3 bg-red-950/40 border border-red-500/40 rounded-lg text-red-300 text-xs">
            {error}
          </div>
        )}

        {/* Upload Card */}
        <section>
          <VideoUpload onUploadSuccess={handleUploadSuccess} />
        </section>

        {/* Video List / Dashboard */}
        <section className="space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-base font-semibold text-white">Processed & Uploaded Videos</h2>
              <p className="text-xs text-slate-400">Select any video to inspect multi-resolution streams and job attempts</p>
            </div>
          </div>

          <VideoList
            videos={videos}
            onSelectVideo={(video) => setSelectedVideo(video)}
            onRefresh={loadVideos}
          />
        </section>
      </main>

      {/* Video Detail Modal */}
      {selectedVideo && (
        <VideoDetailModal
          video={selectedVideo}
          isOpen={Boolean(selectedVideo)}
          onClose={() => setSelectedVideo(null)}
          onVideoUpdated={loadVideos}
        />
      )}

      {/* Health Mesh Modal */}
      <HealthStatus isOpen={isHealthOpen} onClose={() => setIsHealthOpen(false)} />

      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500 bg-slate-950/50">
        <p>Distributed Video Processing Platform • Python 3.12 • FastAPI • RabbitMQ • MySQL 8 • Redis • FFmpeg • React</p>
      </footer>
    </div>
  );
};

export default App;
