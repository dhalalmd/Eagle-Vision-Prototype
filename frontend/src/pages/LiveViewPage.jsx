import React, { useState } from 'react';
import { Grid, Maximize2, X, RefreshCw, AlertCircle } from 'lucide-react';

export default function LiveViewPage({ cameras }) {
  const [layout, setLayout] = useState('auto'); // '1', '2', '4', 'auto'
  const [fullscreenCam, setFullscreenCam] = useState(null);

  const activeCameras = cameras.filter((c) => c.enabled);

  const getGridCols = () => {
    if (layout === '1') return 'grid-cols-1';
    if (layout === '2') return 'grid-cols-1 md:grid-cols-2';
    if (layout === '4') return 'grid-cols-2 lg:grid-cols-2';
    // auto
    if (activeCameras.length <= 1) return 'grid-cols-1';
    if (activeCameras.length <= 4) return 'grid-cols-1 md:grid-cols-2';
    return 'grid-cols-2 lg:grid-cols-3';
  };

  return (
    <div className="p-6 flex-1 flex flex-col h-full overflow-y-auto">
      <div className="flex items-center justify-between mb-5 shrink-0">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Live CCTV Surveillance Grid</h2>
          <p className="text-xs text-gray-400">Real-time multi-camera command stream</p>
        </div>

        <div className="flex items-center space-x-2 bg-gray-900 p-1 rounded-lg border border-gray-800">
          <span className="text-xs text-gray-400 font-medium px-2">Layout:</span>
          {['auto', '1', '2', '4'].map((l) => (
            <button
              key={l}
              onClick={() => setLayout(l)}
              className={`px-3 py-1 rounded text-xs font-semibold uppercase transition-colors ${
                layout === l
                  ? 'bg-sky-600 text-white shadow'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
            >
              {l}
            </button>
          ))}
        </div>
      </div>

      {activeCameras.length === 0 ? (
        <div className="flex-1 bg-gray-900/50 border border-gray-800 rounded-2xl flex flex-col items-center justify-center p-8 text-center">
          <AlertCircle size={40} className="text-amber-500 mb-3" />
          <h3 className="text-base font-semibold text-white">No Active Cameras Configured</h3>
          <p className="text-xs text-gray-400 mt-1 max-w-sm">
            Go to the Cameras tab to enable or add a laptop webcam, phone camera, or RTSP feed.
          </p>
        </div>
      ) : (
        <div className={`grid ${getGridCols()} gap-4 flex-1 auto-rows-fr`}>
          {activeCameras.map((cam) => (
            <CameraTile key={cam.id} camera={cam} onFullscreen={() => setFullscreenCam(cam)} />
          ))}
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
    <div className="bg-[#111827] border border-gray-800 rounded-xl overflow-hidden flex flex-col relative group shadow-lg">
      <div className="px-4 py-2.5 bg-gray-900/90 border-b border-gray-800 flex items-center justify-between z-10 shrink-0">
        <div className="flex items-center space-x-2 truncate">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              camera.status === 'online'
                ? 'bg-emerald-500 animate-pulse'
                : camera.status === 'connecting'
                ? 'bg-amber-500'
                : 'bg-rose-500'
            }`}
          />
          <span className="text-xs font-semibold text-white truncate">{camera.name}</span>
        </div>

        <div className="flex items-center space-x-3">
          <span className="text-[11px] text-gray-400 font-mono">
            {camera.status === 'online' ? `${camera.fps} FPS` : camera.status}
          </span>
          <button
            onClick={onFullscreen}
            className="text-gray-400 hover:text-sky-400 transition-colors"
            title="Fullscreen"
          >
            <Maximize2 size={14} />
          </button>
        </div>
      </div>

      <div className="flex-1 bg-black flex items-center justify-center relative min-h-[220px]">
        {camera.status === 'online' && !error ? (
          <img
            src={`/api/stream/${camera.id}`}
            alt={camera.name}
            onError={() => setError(true)}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex flex-col items-center justify-center p-6 text-center text-gray-500 space-y-2">
            <RefreshCw size={28} className="animate-spin text-gray-600 mb-1" />
            <p className="text-xs font-medium text-gray-400">
              {camera.status === 'connecting' ? 'Connecting to video stream...' : 'Camera Offline'}
            </p>
            <p className="text-[10px] text-gray-600 font-mono">
              ID: {camera.id} | Type: {camera.type}
            </p>
            {error && (
              <button
                onClick={() => setError(false)}
                className="mt-2 text-xs text-sky-400 hover:underline"
              >
                Retry Stream
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
