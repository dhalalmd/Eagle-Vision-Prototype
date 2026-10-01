import React, { useState, useEffect } from 'react';
import { Maximize2, X, RefreshCw, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';

const LAYOUTS = ['1', '2', '4', '9', 'auto'];
const LAYOUT_GRID = { '1': [1,1], '2': [2,1], '4': [2,2], '9': [3,3] };

function getAutoGrid(n) {
  if (n <= 1) return [1, 1];
  const cols = Math.ceil(Math.sqrt(n));
  const rows = Math.ceil(n / cols);
  return [cols, rows];
}

export default function LiveViewPage({ cameras }) {
  const [layout, setLayout] = useState(() => {
    try { return localStorage.getItem('live_layout') || 'auto'; } catch { return 'auto'; }
  });
  const [fullscreenCam, setFullscreenCam] = useState(null);
  const [page, setPage] = useState(0);

  useEffect(() => {
    try { localStorage.setItem('live_layout', layout); } catch {}
  }, [layout]);

  const activeCameras = cameras.filter((c) => c.enabled);
  const n = activeCameras.length;

  // Determine grid size
  let [cols, rows] = layout === 'auto' ? getAutoGrid(n) : LAYOUT_GRID[layout];
  const cells = cols * rows;

  // Paging
  const totalPages = Math.max(1, Math.ceil(n / cells));
  const safePage = Math.min(page, totalPages - 1);
  const startIdx = safePage * cells;
  const visibleCams = activeCameras.slice(startIdx, startIdx + cells);

  // Reset page when cameras change
  useEffect(() => { if (page >= totalPages) setPage(Math.max(0, totalPages - 1)); }, [n, totalPages]);

  // Esc exits fullscreen
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') setFullscreenCam(null); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  return (
    <div className="flex-1 flex flex-col overflow-hidden" style={{ height: 'calc(100vh - 64px)' }}>
      {/* Header row */}
      <div className="flex items-center justify-between px-5 py-3 shrink-0">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight">Live Surveillance</h2>
          <p className="text-[11px] text-gray-500">Real-time multi-camera grid</p>
        </div>

        <div className="flex items-center space-x-1.5 bg-gray-900 p-1 rounded-lg border border-gray-800">
          {LAYOUTS.map((l) => (
            <button
              key={l}
              onClick={() => { setLayout(l); setPage(0); }}
              className={`px-2.5 py-1 rounded text-[11px] font-bold uppercase tracking-wide transition-colors ${
                layout === l
                  ? 'bg-sky-600 text-white shadow'
                  : 'text-gray-500 hover:bg-gray-800 hover:text-white'
              }`}
            >
              {l}
            </button>
          ))}
        </div>
      </div>

      {/* Grid area — fills remaining space, no scroll */}
      {n === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
          <AlertCircle size={36} className="text-amber-500 mb-3" />
          <h3 className="text-sm font-semibold text-white">No Active Cameras</h3>
          <p className="text-[11px] text-gray-500 mt-1 max-w-xs">
            Go to Cameras to enable or add a source.
          </p>
        </div>
      ) : (
        <div className="flex-1 flex flex-col overflow-hidden px-4 pb-3">
          <div
            className="flex-1 grid gap-2 min-h-0"
            style={{
              gridTemplateColumns: `repeat(${cols}, 1fr)`,
              gridTemplateRows: `repeat(${rows}, 1fr)`,
            }}
          >
            {Array.from({ length: cells }).map((_, i) => {
              const cam = visibleCams[i];
              if (cam) {
                return <CameraTile key={cam.id} camera={cam} onFullscreen={() => setFullscreenCam(cam)} />;
              }
              return (
                <div key={`empty-${i}`} className="bg-gray-900/30 border border-gray-800/40 rounded-lg flex items-center justify-center">
                  <span className="text-[11px] text-gray-700">No camera</span>
                </div>
              );
            })}
          </div>

          {/* Pager */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-2 shrink-0">
              <button
                onClick={() => setPage(Math.max(0, safePage - 1))}
                disabled={safePage === 0}
                className="p-1 rounded text-gray-400 hover:text-white disabled:opacity-30"
              >
                <ChevronLeft size={18} />
              </button>
              <span className="text-[11px] text-gray-400 font-medium">
                Page {safePage + 1} / {totalPages}
              </span>
              <button
                onClick={() => setPage(Math.min(totalPages - 1, safePage + 1))}
                disabled={safePage >= totalPages - 1}
                className="p-1 rounded text-gray-400 hover:text-white disabled:opacity-30"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Fullscreen Modal */}
      {fullscreenCam && (
        <div className="fixed inset-0 bg-black/90 z-50 flex flex-col p-4 backdrop-blur-md">
          <div className="flex items-center justify-between mb-3 text-white">
            <div className="flex items-center space-x-3">
              <span className="font-bold text-lg">{fullscreenCam.name}</span>
              <span className="text-xs text-sky-400 bg-sky-950/60 px-2 py-0.5 rounded border border-sky-800">
                {fullscreenCam.id} ({fullscreenCam.type})
              </span>
            </div>
            <button
              onClick={() => setFullscreenCam(null)}
              className="p-2 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white"
            >
              <X size={24} />
            </button>
          </div>
          <div className="flex-1 bg-black rounded-xl overflow-hidden flex items-center justify-center relative">
            <img
              src={`/api/stream/${fullscreenCam.id}`}
              alt={fullscreenCam.name}
              className="max-h-full max-w-full object-contain"
            />
          </div>
        </div>
      )}
    </div>
  );
}

function CameraTile({ camera, onFullscreen }) {
  const [error, setError] = useState(false);

  return (
    <div className="bg-[#111827] border border-gray-800 rounded-lg overflow-hidden flex flex-col relative group min-h-0">
      {/* Header */}
      <div className="px-3 py-1.5 bg-gray-900/90 border-b border-gray-800 flex items-center justify-between z-10 shrink-0">
        <div className="flex items-center space-x-2 truncate min-w-0">
          <span
            className={`w-2 h-2 rounded-full shrink-0 ${
              camera.status === 'online'
                ? 'bg-emerald-500 animate-pulse'
                : camera.status === 'connecting'
                ? 'bg-amber-500'
                : 'bg-rose-500'
            }`}
          />
          <span className="text-[11px] font-semibold text-white truncate">{camera.name}</span>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <span className="text-[10px] text-gray-400 font-mono">
            {camera.status === 'online' ? `${camera.fps} FPS` : camera.status}
          </span>
          <button
            onClick={onFullscreen}
            className="text-gray-500 hover:text-sky-400 transition-colors"
            title="Fullscreen"
          >
            <Maximize2 size={12} />
          </button>
        </div>
      </div>

      {/* Video */}
      <div className="flex-1 bg-black flex items-center justify-center relative min-h-0 overflow-hidden">
        {camera.status === 'online' && !error ? (
          <img
            src={`/api/stream/${camera.id}`}
            alt={camera.name}
            onError={() => setError(true)}
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="flex flex-col items-center justify-center p-3 text-center text-gray-500 space-y-1">
            <RefreshCw size={20} className="animate-spin text-gray-600" />
            <p className="text-[10px] font-medium text-gray-400">
              {camera.status === 'connecting' ? 'Connecting...' : 'Offline'}
            </p>
            {camera.note && (
              <p className="text-[9px] text-gray-600 italic">{camera.note}</p>
            )}
            {error && (
              <button onClick={() => setError(false)} className="text-[10px] text-sky-400 hover:underline">
                Retry
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
