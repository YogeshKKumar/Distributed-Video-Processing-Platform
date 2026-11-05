import React, { useEffect, useState } from 'react';
import { X, CheckCircle2, XCircle, RefreshCw, Server } from 'lucide-react';
import { fetchSystemHealth } from '../services/api';
import { SystemHealthResponse } from '../types';

interface HealthStatusProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HealthStatus: React.FC<HealthStatusProps> = ({ isOpen, onClose }) => {
  const [health, setHealth] = useState<SystemHealthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSystemHealth();
      setHealth(data);
    } catch (err: any) {
      setError(err.message || 'Failed to check system health');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadHealth();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const serviceNames: Record<string, { label: string; desc: string; port: number }> = {
    upload_service: { label: 'Video Upload Service', desc: 'Accepts uploads, validates headers & formats', port: 8001 },
    metadata_service: { label: 'Video Metadata Service', desc: 'Stores dimensions, duration, format & status', port: 8002 },
    orchestrator_service: { label: 'Transcoding Orchestrator', desc: 'Schedules jobs, retries & dead-letter queue', port: 8003 },
    worker_service: { label: 'Transcoding Worker Service', desc: 'FFmpeg transcode engine & dedup lock', port: 8004 },
    thumbnail_service: { label: 'Thumbnail Generation Service', desc: 'FFmpeg snapshot & preview extraction', port: 8005 },
    media_service: { label: 'Media Delivery Service', desc: 'HTTP 206 partial streaming & thumbnail delivery', port: 8006 },
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full shadow-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-800/40">
          <div className="flex items-center space-x-2">
            <Server className="w-5 h-5 text-sky-400" />
            <h3 className="font-semibold text-white">Microservices Health Mesh</h3>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={loadHealth}
              disabled={loading}
              className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-700 transition"
              title="Refresh Health"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-sky-400' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-700 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
          {error && (
            <div className="p-3 bg-red-950/50 border border-red-500/40 rounded-lg text-red-300 text-sm flex items-center gap-2">
              <XCircle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="bg-slate-800/50 border border-slate-700/60 rounded-lg p-4 flex items-center justify-between">
            <div>
              <div className="font-medium text-white flex items-center gap-2">
                <span>API Gateway Service</span>
                <span className="text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded">Port 8000</span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">Reverse proxy, CORS & request routing hub</p>
            </div>
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="w-3.5 h-3.5" />
              ACTIVE
            </span>
          </div>

          <div className="space-y-2.5">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Independent Downstream Services</h4>

            {health &&
              Object.entries(health.microservices).map(([key, info]) => {
                const meta = serviceNames[key] || { label: key, desc: 'Microservice', port: 0 };
                const isUp = info.status === 'UP';

                return (
                  <div
                    key={key}
                    className="bg-slate-800/30 border border-slate-800 hover:border-slate-700 rounded-lg p-3.5 flex items-center justify-between transition"
                  >
                    <div>
                      <div className="font-medium text-slate-200 text-sm flex items-center gap-2">
                        {meta.label}
                        {meta.port > 0 && (
                          <span className="text-[11px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700">
                            Port {meta.port}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">{meta.desc}</p>
                    </div>

                    <div>
                      {isUp ? (
                        <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 className="w-3 h-3" />
                          ONLINE
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20" title={info.error}>
                          <XCircle className="w-3 h-3" />
                          OFFLINE
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
          </div>

          <div className="p-3 bg-slate-800/30 rounded-lg border border-slate-800 text-xs text-slate-400 space-y-1">
            <p className="font-semibold text-slate-300">Architecture Isolation Note:</p>
            <p>Each microservice owns its private database (<code className="text-sky-300">upload_db</code>, <code className="text-sky-300">metadata_db</code>, etc.) and communicates asynchronously via RabbitMQ topic exchanges.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
