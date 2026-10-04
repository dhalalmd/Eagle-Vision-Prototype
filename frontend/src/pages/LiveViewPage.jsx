import React, { useState, useEffect, useRef } from 'react';
import { Maximize2, X, RefreshCw, AlertCircle, ChevronLeft, ChevronRight, PenTool, Trash2, Check, ShieldAlert } from 'lucide-react';

const LAYOUTS = ['1', '2', '4', '9', 'auto'];
const LAYOUT_GRID = { '1': [1,1], '2': [2,1], '4': [2,2], '9': [3,3] };

function getAutoGrid(n) {
  if (n <= 1) return [1, 1];
  const cols = Math.ceil(Math.sqrt(n));
  const rows = Math.ceil(n / cols);
  return [cols, rows];
}

export default function LiveViewPage({ cameras, alertCameras = {} }) {
  const [layout, setLayout] = useState(() => {
    try { return localStorage.getItem('live_layout') || 'auto'; } catch { return 'auto'; }
  });
  const [fullscreenCam, setFullscreenCam] = useState(null);
  const [page, setPage] = useState(0);

  // Zone drawing state
  const [drawingCam, setDrawingCam] = useState(null);
  const [drawnPoints, setDrawnPoints] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [zoneName, setZoneName] = useState('');
  const [zoneClasses, setZoneClasses] = useState(['person', 'vehicle']);
  const [cameraZones, setCameraZones] = useState([]);

  useEffect(() => {
    try { localStorage.setItem('live_layout', layout); } catch {}
  }, [layout]);

  const activeCameras = cameras.filter((c) => c.enabled);
  const n = activeCameras.length;

  let [cols, rows] = layout === 'auto' ? getAutoGrid(n) : LAYOUT_GRID[layout];
  const cells = cols * rows;

  const totalPages = Math.max(1, Math.ceil(n / cells));
  const safePage = Math.min(page, totalPages - 1);
  const startIdx = safePage * cells;
  const visibleCams = activeCameras.slice(startIdx, startIdx + cells);

  useEffect(() => { if (page >= totalPages) setPage(Math.max(0, totalPages - 1)); }, [n, totalPages]);

  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') setFullscreenCam(null); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const startDrawZone = (cam) => {
    setDrawingCam(cam);
    setDrawnPoints([]);
    fetchZones(cam.id);
  };

  const fetchZones = async (camId) => {
    try {
      const res = await fetch(`/api/zones?camera_id=${camId}`);
      if (res.ok) {
        const data = await res.json();
        setCameraZones(data);
      }
    } catch (e) {}
  };

  const handleCanvasClick = (e, rect) => {
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    setDrawnPoints((prev) => [...prev, [round(x), round(y)]]);
  };

  const round = (val) => Math.round(val * 1000) / 1000;

  const handleFinishZone = () => {
    if (drawnPoints.length < 3) return;
    setZoneName(`Zone ${cameraZones.length + 1}`);
    setIsModalOpen(true);
  };

  const handleSaveZone = async () => {
    if (!drawingCam || drawnPoints.length < 3) return;
    try {
      const payload = {
        camera_id: drawingCam.id,
        name: zoneName || 'New Zone',
        points: drawnPoints,
        classes: zoneClasses,
        enabled: true,
      };
      const res = await fetch('/api/zones', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        setIsModalOpen(false);
        setDrawnPoints([]);
        fetchZones(drawingCam.id);
      }
    } catch (e) {
      console.error('Failed to save zone:', e);
    }
  };

  const handleDeleteZone = async (zoneId) => {
    try {
      const res = await fetch(`/api/zones/${zoneId}`, { method: 'DELETE' });
      if (res.ok && drawingCam) {
        fetchZones(drawingCam.id);
      }
    } catch (e) {}
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden" style={{ height: 'calc(100vh - 64px)' }}>
      {/* Header row */}
      <div className="flex items-center justify-between px-5 py-3 shrink-0">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight">Live Surveillance</h2>
          <p className="text-[11px] text-gray-500">Real-time multi-camera grid with intrusion detection zones</p>
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

      {/* Grid area */}
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
                const hasRecentAlert = Boolean(alertCameras[cam.id]);

                return (
                  <CameraTile
                    key={cam.id}
                    camera={cam}
                    hasAlert={hasRecentAlert}
                    onFullscreen={() => setFullscreenCam(cam)}
                    onDrawZone={() => startDrawZone(cam)}
                  />
                );
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

      {/* Zone Drawer Canvas Modal */}
      {drawingCam && (
        <div className="fixed inset-0 bg-black/80 z-50 flex flex-col p-4 backdrop-blur-md">
          <div className="flex items-center justify-between mb-2 text-white">
            <div>
              <h3 className="font-bold text-lg flex items-center gap-2">
                <PenTool className="w-5 h-5 text-indigo-400" />
                Draw Intrusion Zone — {drawingCam.name}
              </h3>
              <p className="text-xs text-gray-400">Click 3 or more points on the video tile to form a boundary polygon.</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleFinishZone}
                disabled={drawnPoints.length < 3}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-xs font-semibold rounded-lg flex items-center gap-1"
              >
                <Check className="w-4 h-4" /> Save Zone ({drawnPoints.length} pts)
              </button>
              <button
                onClick={() => setDrawingCam(null)}
                className="p-2 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white"
              >
                <X size={22} />
              </button>
            </div>
          </div>

          <div className="flex-1 flex gap-4 overflow-hidden">
            {/* Interactive Canvas */}
            <div
              className="flex-1 bg-black rounded-xl overflow-hidden relative cursor-crosshair border border-indigo-500/50"
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                handleCanvasClick(e, rect);
              }}
            >
              <img
                src={`/api/stream/${drawingCam.id}`}
                alt={drawingCam.name}
                className="w-full h-full object-contain pointer-events-none"
              />

              {/* Overlay SVG points and polygon */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none">
                {drawnPoints.length > 0 && (
                  <polygon
                    points={drawnPoints.map(([x, y]) => `${x * 100}% ${y * 100}%`).join(' ')}
                    fill="rgba(239, 68, 68, 0.25)"
                    stroke="#ef4444"
                    strokeWidth="2.5"
                  />
                )}
                {drawnPoints.map(([x, y], idx) => (
                  <circle
                    key={idx}
                    cx={`${x * 100}%`}
                    cy={`${y * 100}%`}
                    r="5"
                    fill="#38bdf8"
                    stroke="#ffffff"
                    strokeWidth="2"
                  />
                ))}
              </svg>
            </div>

            {/* Existing Zones Sidebar */}
            <div className="w-64 bg-[#111827] border border-gray-800 rounded-xl p-4 flex flex-col text-xs text-gray-200">
              <h4 className="font-bold text-white mb-2 pb-2 border-b border-gray-800">
                Active Camera Zones
              </h4>
              <div className="flex-1 overflow-y-auto space-y-2">
                {cameraZones.length === 0 ? (
                  <p className="text-gray-500 italic">No zones saved for this camera yet.</p>
                ) : (
                  cameraZones.map((z) => (
                    <div key={z.id} className="p-2.5 bg-gray-900 rounded border border-gray-800 flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-white">{z.name}</p>
                        <p className="text-[10px] text-gray-400 capitalize">
                          Classes: {Array.isArray(z.classes) ? z.classes.join(', ') : 'person, vehicle'}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteZone(z.id)}
                        className="text-rose-400 hover:text-rose-300 p-1"
                        title="Delete Zone"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Zone Config Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
          <div className="bg-[#121826] border border-gray-800 rounded-xl p-6 w-full max-w-md text-gray-100">
            <h3 className="text-lg font-bold text-white mb-4">Configure Intrusion Zone</h3>

            <div className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-300 font-semibold mb-1">Zone Name:</label>
                <input
                  type="text"
                  value={zoneName}
                  onChange={(e) => setZoneName(e.target.value)}
                  className="w-full p-2 bg-gray-900 border border-gray-700 rounded text-white"
                  placeholder="e.g. Border Line Alpha"
                />
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-2">Target Object Classes:</label>
                <div className="grid grid-cols-2 gap-2">
                  {['person', 'vehicle', 'animal', 'object'].map((cls) => {
                    const checked = zoneClasses.includes(cls);
                    return (
                      <label key={cls} className="flex items-center gap-2 cursor-pointer text-gray-300">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(e) => {
                            if (e.target.checked) setZoneClasses((prev) => [...prev, cls]);
                            else setZoneClasses((prev) => prev.filter((c) => c !== cls));
                          }}
                          className="rounded border-gray-700 bg-gray-900 text-indigo-600"
                        />
                        <span className="capitalize">{cls}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs rounded-lg font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveZone}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs rounded-lg font-semibold"
              >
                Save Zone
              </button>
            </div>
          </div>
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

function CameraTile({ camera, hasAlert, onFullscreen, onDrawZone }) {
  const [error, setError] = useState(false);

  return (
    <div
      className={`bg-[#111827] rounded-lg overflow-hidden flex flex-col relative group min-h-0 transition-all ${
        hasAlert
          ? 'border-2 border-rose-500 animate-pulse shadow-lg shadow-rose-950/50'
          : 'border border-gray-800'
      }`}
    >
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
          <button
            onClick={onDrawZone}
            className="text-gray-400 hover:text-sky-400 transition-colors text-[10px] flex items-center gap-1 bg-gray-800 px-1.5 py-0.5 rounded border border-gray-700"
            title="Draw Intrusion Zone"
          >
            <PenTool size={10} />
            <span>Zone</span>
          </button>
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
