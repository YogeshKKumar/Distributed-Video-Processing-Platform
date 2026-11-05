import React, { useState, useRef } from 'react';
import { UploadCloud, Film, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { uploadVideo } from '../services/api';

interface VideoUploadProps {
  onUploadSuccess: (videoId: string) => void;
}

const ALLOWED_EXTS = ['.mp4', '.mov', '.avi', '.mkv', '.webm'];
const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500 MB

export const VideoUpload: React.FC<VideoUploadProps> = ({ onUploadSuccess }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): boolean => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTS.includes(ext)) {
      setError(`Unsupported file type '${ext}'. Permitted: ${ALLOWED_EXTS.join(', ')}`);
      return false;
    }
    if (file.size <= 0) {
      setError('File is empty. Please select a valid video.');
      return false;
    }
    if (file.size > MAX_FILE_SIZE) {
      setError(`File size exceeds the 500MB limit (${(file.size / (1024 * 1024)).toFixed(1)}MB).`);
      return false;
    }
    setError(null);
    return true;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
        if (!title) {
          setTitle(file.name.replace(/\.[^/.]+$/, ''));
        }
      }
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
        if (!title) {
          setTitle(file.name.replace(/\.[^/.]+$/, ''));
        }
      }
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsUploading(true);
    setProgress(0);
    setError(null);
    setSuccess(null);

    try {
      const result = await uploadVideo(selectedFile, title, (pct) => setProgress(pct));
      setSuccess(`Video "${title || selectedFile.name}" uploaded successfully! Asynchronous processing initiated.`);
      setSelectedFile(null);
      setTitle('');
      if (inputRef.current) inputRef.current.value = '';
      onUploadSuccess(result.video_id);
    } catch (err: any) {
      setError(err.message || 'Failed to upload video');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-slate-800/40 border border-slate-800 rounded-xl p-6 shadow-xl">
      <h2 className="text-base font-semibold text-white mb-2 flex items-center gap-2">
        <Film className="w-5 h-5 text-sky-400" />
        Upload Video for Distributed Transcoding
      </h2>
      <p className="text-xs text-slate-400 mb-5">
        Upload MP4, MOV, MKV, AVI, or WebM files up to 500MB. Transcoding into 360p, 720p, 1080p and thumbnail extraction run asynchronously.
      </p>

      {error && (
        <div className="mb-4 p-3 bg-red-950/40 border border-red-500/40 rounded-lg text-red-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-emerald-950/40 border border-emerald-500/40 rounded-lg text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      <form onSubmit={handleUpload} className="space-y-4">
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition ${
            dragActive
              ? 'border-sky-500 bg-sky-950/20'
              : selectedFile
              ? 'border-emerald-500/60 bg-emerald-950/10'
              : 'border-slate-700 hover:border-slate-600 bg-slate-900/40'
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".mp4,.mov,.avi,.mkv,.webm"
            onChange={handleFileChange}
            className="hidden"
            disabled={isUploading}
          />

          <div className="flex flex-col items-center space-y-2">
            <UploadCloud className={`w-10 h-10 ${selectedFile ? 'text-emerald-400' : 'text-slate-400'}`} />
            {selectedFile ? (
              <div>
                <p className="text-sm font-medium text-emerald-300">{selectedFile.name}</p>
                <p className="text-xs text-slate-400">{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
              </div>
            ) : (
              <div>
                <p className="text-sm font-medium text-slate-300">Drag & drop your video here, or browse files</p>
                <p className="text-xs text-slate-500 mt-1">MP4, MOV, MKV, AVI, WebM (Max 500MB)</p>
              </div>
            )}
          </div>
        </div>

        {selectedFile && (
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Video Title (Optional)</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter a descriptive title"
                disabled={isUploading}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 transition"
              />
            </div>

            {isUploading && (
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Uploading to Gateway...</span>
                  <span className="font-semibold text-sky-400">{progress}%</span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                  <div
                    className="bg-gradient-to-r from-sky-500 to-indigo-500 h-2 transition-all duration-200"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={isUploading}
              className="w-full flex items-center justify-center space-x-2 bg-sky-600 hover:bg-sky-500 text-white font-medium py-2.5 px-4 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-sky-900/30"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Uploading & Scheduling...</span>
                </>
              ) : (
                <span>Upload & Start Processing</span>
              )}
            </button>
          </div>
        )}
      </form>
    </div>
  );
};
