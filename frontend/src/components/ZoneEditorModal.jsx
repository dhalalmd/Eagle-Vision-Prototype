import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  X, Check, Undo, Redo, Trash2, ArrowRightLeft, Move,
  Maximize2, PenTool, ShieldAlert, AlertTriangle, RefreshCw, Edit3
} from 'lucide-react';

function checkSegmentIntersection(p1, p2, p3, p4) {
  function ccw(a, b, c) {
    return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0]);
  }
  return (ccw(p1, p3, p4) !== ccw(p2, p3, p4)) && (ccw(p1, p2, p3) !== ccw(p1, p2, p4));
}

function validateGeometry(points, type) {
  if (type === 'line') {
    if (!points || points.length < 2) return { valid: false, message: 'Line tripwire requires at least 2 points.' };
    return { valid: true, message: '' };
  }

  if (!points || points.length < 3) {
    return { valid: false, message: 'Polygon requires at least 3 vertices.' };
  }

  // Calculate area using Shoelace formula
  const n = points.length;
  let area = 0;
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    area += points[i][0] * points[j][1] - points[j][0] * points[i][1];
  }
  area = Math.abs(area) * 0.5;

  if (area < 0.0005) {
    return { valid: false, message: 'Shape area is too small.' };
  }

  // Check self-intersection for non-adjacent edges
  const edges = [];
  for (let i = 0; i < n; i++) {
    edges.push([points[i], points[(i + 1) % n]]);
  }

  for (let i = 0; i < n; i++) {
    for (let j = i + 2; j < n; j++) {
      if (i === 0 && j === n - 1) continue; // Skip adjacent start-end edges
      if (checkSegmentIntersection(edges[i][0], edges[i][1], edges[j][0], edges[j][1])) {
        return { valid: false, message: 'Polygon has self-intersecting edges.' };
      }
    }
  }

  return { valid: true, message: '' };
}

function clamp(val, min = 0, max = 1) {
  return Math.max(min, Math.min(max, val));
}

export default function ZoneEditorModal({ camera, zone, onClose, onSave }) {
  const isEditing = Boolean(zone && zone.id);

  // Initial zone state snapshot for Cancel restoration
  const initialPoints = zone?.points ? zone.points.map((p) => [...p]) : [
    [0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]
  ];

  const [points, setPoints] = useState(initialPoints);
  const [name, setName] = useState(zone?.name || (isEditing ? zone.name : 'New Security Zone'));
  const [classes, setClasses] = useState(zone?.classes || ['person', 'vehicle']);
  const [enabled, setEnabled] = useState(zone?.enabled !== false);
  const [type, setType] = useState(zone?.type || 'polygon');
  const [color, setColor] = useState(zone?.color || '#ef4444');
  const [direction, setDirection] = useState(zone?.direction || 'both');
  const [activeZoneId, setActiveZoneId] = useState(zone?.id || null);

  const [cameraZones, setCameraZones] = useState([]);
  const [selectedVertex, setSelectedVertex] = useState(null);
  const [dragState, setDragState] = useState(null); // { mode: 'vertex'|'midpoint'|'shape'|'rect_handle', ... }

  // History stack for Undo / Redo
  const [history, setHistory] = useState([initialPoints]);
  const [historyIdx, setHistoryIdx] = useState(0);

  const containerRef = useRef(null);

  const fetchCameraZones = useCallback(async () => {
    if (!camera?.id) return;
    try {
      const res = await fetch(`/api/zones?camera_id=${camera.id}`);
      if (res.ok) {
        const data = await res.json();
        setCameraZones(data);
      }
    } catch (e) {
      console.error('Failed to fetch camera zones:', e);
    }
  }, [camera?.id]);

  useEffect(() => {
    fetchCameraZones();
  }, [fetchCameraZones]);

  const loadZoneIntoEditor = (z) => {
    setActiveZoneId(z.id);
    const loadedPts = z.points.map((p) => [...p]);
    setPoints(loadedPts);
    setName(z.name || `Zone ${z.id}`);
    setType(z.type || 'polygon');
    setColor(z.color || '#ef4444');
    setClasses(z.classes || ['person', 'vehicle']);
    setEnabled(z.enabled !== false);
    setDirection(z.direction || 'both');
    setSelectedVertex(null);
    setHistory([loadedPts]);
    setHistoryIdx(0);
  };

  const startNewZone = () => {
    setActiveZoneId(null);
    const newPts = [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]];
    setPoints(newPts);
    setName('New Security Zone');
    setType('polygon');
    setColor('#ef4444');
    setClasses(['person', 'vehicle']);
    setEnabled(true);
    setDirection('both');
    setSelectedVertex(null);
    setHistory([newPts]);
    setHistoryIdx(0);
  };

  const pushState = (newPoints) => {
    const nextHistory = history.slice(0, historyIdx + 1);
    nextHistory.push(newPoints);
    setHistory(nextHistory);
    setHistoryIdx(nextHistory.length - 1);
    setPoints(newPoints);
  };

  const handleUndo = useCallback(() => {
    if (historyIdx > 0) {
      setHistoryIdx(historyIdx - 1);
      setPoints(history[historyIdx - 1]);
    }
  }, [history, historyIdx]);

  const handleRedo = useCallback(() => {
    if (historyIdx < history.length - 1) {
      setHistoryIdx(historyIdx + 1);
      setPoints(history[historyIdx + 1]);
    }
  }, [history, historyIdx]);

  // Validation state
  const validation = validateGeometry(points, type);

  // Convert client (X, Y) relative to container to normalized (0-1) coordinates inside letterboxed video
  const clientToNormalized = (clientX, clientY) => {
    if (!containerRef.current) return [0, 0];
    const rect = containerRef.current.getBoundingClientRect();
    const containerWidth = rect.width;
    const containerHeight = rect.height;

    const aspect = 16 / 9;
    let imgWidth = containerWidth;
    let imgHeight = containerWidth / aspect;

    if (imgHeight > containerHeight) {
      imgHeight = containerHeight;
      imgWidth = containerHeight * aspect;
    }

    const offsetX = (containerWidth - imgWidth) / 2;
    const offsetY = (containerHeight - imgHeight) / 2;

    const relX = clientX - rect.left - offsetX;
    const relY = clientY - rect.top - offsetY;

    const normX = clamp(relX / imgWidth, 0, 1);
    const normY = clamp(relY / imgHeight, 0, 1);

    return [Math.round(normX * 1000) / 1000, Math.round(normY * 1000) / 1000];
  };

  // Drag handlers
  const handleMouseDownVertex = (idx, e) => {
    e.stopPropagation();
    setSelectedVertex(idx);
    setDragState({
      mode: 'vertex',
      index: idx,
      startPoints: [...points.map((p) => [...p])],
    });
  };

  const handleMouseDownMidpoint = (idx, e) => {
    e.stopPropagation();
    const p1 = points[idx];
    const p2 = points[(idx + 1) % points.length];
    const midPoint = [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2];

    const newPoints = [...points];
    newPoints.splice(idx + 1, 0, midPoint);

    const newIdx = idx + 1;
    setSelectedVertex(newIdx);
    pushState(newPoints);

    setDragState({
      mode: 'vertex',
      index: newIdx,
      startPoints: newPoints.map((p) => [...p]),
    });
  };

  const handleMouseDownShape = (e) => {
    e.stopPropagation();
    const [nx, ny] = clientToNormalized(e.clientX, e.clientY);
    setDragState({
      mode: 'shape',
      startNorm: [nx, ny],
      startPoints: points.map((p) => [...p]),
    });
  };

  const handleMouseDownRectHandle = (handleKey, e) => {
    e.stopPropagation();
    setDragState({
      mode: 'rect_handle',
      handle: handleKey,
      startPoints: points.map((p) => [...p]),
    });
  };

  const handleMouseMove = (e) => {
    if (!dragState) return;

    const [nx, ny] = clientToNormalized(e.clientX, e.clientY);

    if (dragState.mode === 'vertex') {
      const newPoints = points.map((p, i) => (i === dragState.index ? [nx, ny] : p));
      setPoints(newPoints);
    } else if (dragState.mode === 'shape') {
      const [startNx, startNy] = dragState.startNorm;
      const dx = nx - startNx;
      const dy = ny - startNy;

      // Calculate max allowed translation without exceeding [0, 1] bounds
      let minX = 1, maxX = 0, minY = 1, maxY = 0;
      dragState.startPoints.forEach(([px, py]) => {
        minX = Math.min(minX, px);
        maxX = Math.max(maxX, px);
        minY = Math.min(minY, py);
        maxY = Math.max(maxY, py);
      });

      const clampedDx = Math.max(-minX, Math.min(1 - maxX, dx));
      const clampedDy = Math.max(-minY, Math.min(1 - maxY, dy));

      const newPoints = dragState.startPoints.map(([px, py]) => [
        clamp(px + clampedDx, 0, 1),
        clamp(py + clampedDy, 0, 1),
      ]);
      setPoints(newPoints);
    } else if (dragState.mode === 'rect_handle') {
      const [p0, p1, p2, p3] = dragState.startPoints;
      let minX = Math.min(p0[0], p1[0], p2[0], p3[0]);
      let maxX = Math.max(p0[0], p1[0], p2[0], p3[0]);
      let minY = Math.min(p0[1], p1[1], p2[1], p3[1]);
      let maxY = Math.max(p0[1], p1[1], p2[1], p3[1]);

      const handle = dragState.handle;
      if (handle.includes('n')) minY = clamp(ny, 0, maxY - 0.02);
      if (handle.includes('s')) maxY = clamp(ny, minY + 0.02, 1);
      if (handle.includes('w')) minX = clamp(nx, 0, maxX - 0.02);
      if (handle.includes('e')) maxX = clamp(nx, minX + 0.02, 1);

      const rectPoints = [
        [minX, minY],
        [maxX, minY],
        [maxX, maxY],
        [minX, maxY],
      ];
      setPoints(rectPoints);
    }
  };

  const handleMouseUp = () => {
    if (dragState) {
      pushState(points);
      setDragState(null);
    }
  };

  // Delete selected vertex (polygons keep at least 3 points, lines keep 2)
  const handleDeleteVertex = (idxToDelete) => {
    const targetIdx = idxToDelete != null ? idxToDelete : selectedVertex;
    if (targetIdx == null) return;

    const minRequired = type === 'line' ? 2 : 3;
    if (points.length <= minRequired) return;

    const newPoints = points.filter((_, i) => i !== targetIdx);
    setSelectedVertex(null);
    pushState(newPoints);
  };

  // Convert Rectangle to free polygon
  const handleConvertToPolygon = () => {
    setType('polygon');
  };

  // Flip Line tripwire direction
  const handleFlipDirection = () => {
    if (points.length >= 2) {
      const reversed = [...points].reverse();
      pushState(reversed);
    }
    setDirection((d) => (d === 'left_to_right' ? 'right_to_left' : d === 'right_to_left' ? 'both' : 'left_to_right'));
  };

  // Nudge logic via Arrow Keys (1px / Shift 10px)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
        if (e.shiftKey) handleRedo();
        else handleUndo();
        e.preventDefault();
        return;
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'y') {
        handleRedo();
        e.preventDefault();
        return;
      }

      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (selectedVertex !== null && document.activeElement.tagName !== 'INPUT') {
          handleDeleteVertex(selectedVertex);
          e.preventDefault();
        }
        return;
      }

      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
        if (document.activeElement.tagName === 'INPUT') return;
        e.preventDefault();

        const step = e.shiftKey ? 0.01 : 0.001; // 10px or 1px normalized
        let dx = 0, dy = 0;
        if (e.key === 'ArrowLeft') dx = -step;
        if (e.key === 'ArrowRight') dx = step;
        if (e.key === 'ArrowUp') dy = -step;
        if (e.key === 'ArrowDown') dy = step;

        if (selectedVertex !== null) {
          const newPoints = points.map((p, i) =>
            i === selectedVertex ? [clamp(p[0] + dx, 0, 1), clamp(p[1] + dy, 0, 1)] : p
          );
          pushState(newPoints);
        } else {
          // Nudge whole zone
          let minX = 1, maxX = 0, minY = 1, maxY = 0;
          points.forEach(([px, py]) => {
            minX = Math.min(minX, px);
            maxX = Math.max(maxX, px);
            minY = Math.min(minY, py);
            maxY = Math.max(maxY, py);
          });
          const clampedDx = Math.max(-minX, Math.min(1 - maxX, dx));
          const clampedDy = Math.max(-minY, Math.min(1 - maxY, dy));

          const newPoints = points.map(([px, py]) => [
            clamp(px + clampedDx, 0, 1),
            clamp(py + clampedDy, 0, 1),
          ]);
          pushState(newPoints);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedVertex, points, handleUndo, handleRedo]);

  const handleSave = () => {
    if (!validation.valid) return;

    const payload = {
      id: activeZoneId,
      camera_id: camera.id,
      name: name || 'Security Zone',
      points,
      classes,
      enabled,
      type,
      color,
      direction,
    };
    onSave(payload);
  };

  // Compute bounding box for rectangles
  const rectMinX = Math.min(...points.map((p) => p[0]));
  const rectMaxX = Math.max(...points.map((p) => p[0]));
  const rectMinY = Math.min(...points.map((p) => p[1]));
  const rectMaxY = Math.max(...points.map((p) => p[1]));

  const rectHandles = [
    { key: 'nw', x: rectMinX, y: rectMinY },
    { key: 'n',  x: (rectMinX + rectMaxX) / 2, y: rectMinY },
    { key: 'ne', x: rectMaxX, y: rectMinY },
    { key: 'e',  x: rectMaxX, y: (rectMinY + rectMaxY) / 2 },
    { key: 'se', x: rectMaxX, y: rectMaxY },
    { key: 's',  x: (rectMinX + rectMaxX) / 2, y: rectMaxY },
    { key: 'sw', x: rectMinX, y: rectMaxY },
    { key: 'w',  x: rectMinX, y: (rectMinY + rectMaxY) / 2 },
  ];

  return (
    <div className="fixed inset-0 bg-black/85 z-50 flex flex-col p-4 backdrop-blur-md select-none">
      {/* Top Header */}
      <div className="flex items-center justify-between mb-3 text-white shrink-0">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-indigo-600/20 text-indigo-400 rounded-lg border border-indigo-500/30">
            <PenTool size={20} />
          </div>
          <div>
            <h3 className="font-bold text-lg text-white">
              {activeZoneId ? `Edit Zone — "${name}"` : `Draw New Zone — ${camera.name}`}
            </h3>
            <p className="text-xs text-gray-400">
              Drag handles to move vertices, click midpoints to insert points, or drag shape to move whole zone.
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleUndo}
            disabled={historyIdx === 0}
            className="p-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-30 text-gray-300 rounded-lg border border-gray-700 transition"
            title="Undo (Ctrl+Z)"
          >
            <Undo size={16} />
          </button>
          <button
            onClick={handleRedo}
            disabled={historyIdx === history.length - 1}
            className="p-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-30 text-gray-300 rounded-lg border border-gray-700 transition"
            title="Redo (Ctrl+Y)"
          >
            <Redo size={16} />
          </button>

          <div className="h-5 w-px bg-gray-700 mx-1" />

          <button
            onClick={onClose}
            className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs font-semibold rounded-lg border border-gray-700 transition"
          >
            Cancel
          </button>

          <button
            onClick={handleSave}
            disabled={!validation.valid}
            className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-xs font-semibold rounded-lg shadow-md transition flex items-center gap-1.5"
          >
            <Check size={16} />
            Save Zone
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex gap-4 overflow-hidden min-h-0">
        {/* Editor Canvas */}
        <div className="flex-1 flex flex-col bg-[#0d121f] rounded-xl border border-gray-800 overflow-hidden relative">
          {/* Validation Banner */}
          {!validation.valid && (
            <div className="bg-rose-500/10 border-b border-rose-500/30 px-4 py-2 text-rose-400 text-xs font-semibold flex items-center gap-2 z-20">
              <AlertTriangle size={16} />
              <span>{validation.message}</span>
            </div>
          )}

          {/* Interactive Stream Canvas Container */}
          <div
            ref={containerRef}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            className="flex-1 w-full h-full bg-black relative flex items-center justify-center overflow-hidden"
          >
            {/* Frozen / Live Camera Image */}
            <img
              src={`/api/stream/${camera.id}`}
              alt={camera.name}
              className="max-h-full max-w-full object-contain pointer-events-none select-none"
            />

            {/* Interactive SVG Overlay */}
            <svg
              className="absolute inset-0 w-full h-full"
              onMouseDown={() => setSelectedVertex(null)}
            >
              {/* Shape Fill & Perimeter Stroke */}
              {type === 'line' ? (
                <line
                  x1={`${points[0][0] * 100}%`}
                  y1={`${points[0][1] * 100}%`}
                  x2={`${points[1][0] * 100}%`}
                  y2={`${points[1][1] * 100}%`}
                  stroke={validation.valid ? color : '#ef4444'}
                  strokeWidth="3.5"
                  strokeDasharray="6 4"
                  className="cursor-move"
                  onMouseDown={handleMouseDownShape}
                />
              ) : (
                <polygon
                  points={points.map(([x, y]) => `${x * 100}% ${y * 100}%`).join(' ')}
                  fill={validation.valid ? `${color}33` : '#ef444433'}
                  stroke={validation.valid ? color : '#ef4444'}
                  strokeWidth="2.5"
                  className="cursor-move"
                  onMouseDown={handleMouseDownShape}
                />
              )}

              {/* Edge Midpoint Handles (for insertion) */}
              {type === 'polygon' &&
                points.map((p, idx) => {
                  const pNext = points[(idx + 1) % points.length];
                  const midX = (p[0] + pNext[0]) / 2;
                  const midY = (p[1] + pNext[1]) / 2;
                  return (
                    <circle
                      key={`mid-${idx}`}
                      cx={`${midX * 100}%`}
                      cy={`${midY * 100}%`}
                      r="4"
                      fill="#38bdf8"
                      stroke="#ffffff"
                      strokeWidth="1.5"
                      className="cursor-pointer hover:scale-125 transition-transform opacity-70 hover:opacity-100"
                      onMouseDown={(e) => handleMouseDownMidpoint(idx, e)}
                    />
                  );
                })}

              {/* Vertex Handles */}
              {type === 'rectangle'
                ? rectHandles.map((h) => (
                    <rect
                      key={h.key}
                      x={`calc(${h.x * 100}% - 5px)`}
                      y={`calc(${h.y * 100}% - 5px)`}
                      width="10"
                      height="10"
                      fill="#38bdf8"
                      stroke="#ffffff"
                      strokeWidth="2"
                      className="cursor-pointer hover:scale-125 transition-transform"
                      onMouseDown={(e) => handleMouseDownRectHandle(h.key, e)}
                    />
                  ))
                : points.map(([x, y], idx) => {
                    const isSelected = selectedVertex === idx;
                    return (
                      <g key={`vertex-${idx}`}>
                        <circle
                          cx={`${x * 100}%`}
                          cy={`${y * 100}%`}
                          r={isSelected ? '7' : '5'}
                          fill={isSelected ? '#f59e0b' : '#38bdf8'}
                          stroke="#ffffff"
                          strokeWidth="2"
                          className="cursor-pointer hover:scale-125 transition-transform"
                          onMouseDown={(e) => handleMouseDownVertex(idx, e)}
                          onContextMenu={(e) => {
                            e.preventDefault();
                            handleDeleteVertex(idx);
                          }}
                        />
                      </g>
                    );
                  })}
            </svg>
          </div>
        </div>

        {/* Right Settings Sidebar */}
        <div className="w-80 bg-[#101625] border border-gray-800 rounded-xl p-4 flex flex-col shrink-0 overflow-y-auto text-xs space-y-4">
          <h4 className="font-bold text-white text-sm pb-2 border-b border-gray-800">
            Zone Properties
          </h4>

          {/* Name */}
          <div>
            <label className="block text-gray-400 font-semibold mb-1">Zone Name:</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full p-2 bg-gray-900 border border-gray-700 rounded-lg text-white font-medium"
              placeholder="e.g. Fence Line Alpha"
            />
          </div>

          {/* Type Selector */}
          <div>
            <label className="block text-gray-400 font-semibold mb-1">Shape Type:</label>
            <div className="grid grid-cols-3 gap-1 bg-gray-900 p-1 rounded-lg border border-gray-800">
              <button
                onClick={() => {
                  setType('polygon');
                  if (points.length < 3) {
                    pushState([[0.3, 0.3], [0.7, 0.3], [0.7, 0.7], [0.3, 0.7]]);
                  }
                }}
                className={`py-1 rounded text-[11px] font-semibold transition ${
                  type === 'polygon' ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'
                }`}
              >
                Polygon
              </button>
              <button
                onClick={() => {
                  setType('rectangle');
                  const minX = Math.min(...points.map((p) => p[0]));
                  const maxX = Math.max(...points.map((p) => p[0]));
                  const minY = Math.min(...points.map((p) => p[1]));
                  const maxY = Math.max(...points.map((p) => p[1]));
                  pushState([[minX, minY], [maxX, minY], [maxX, maxY], [minX, maxY]]);
                }}
                className={`py-1 rounded text-[11px] font-semibold transition ${
                  type === 'rectangle' ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'
                }`}
              >
                Rectangle
              </button>
              <button
                onClick={() => {
                  setType('line');
                  if (points.length !== 2) {
                    pushState([[0.2, 0.5], [0.8, 0.5]]);
                  }
                }}
                className={`py-1 rounded text-[11px] font-semibold transition ${
                  type === 'line' ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'
                }`}
              >
                Tripwire
              </button>
            </div>
          </div>

          {/* Color Picker */}
          <div>
            <label className="block text-gray-400 font-semibold mb-1">Zone Color:</label>
            <div className="flex items-center gap-2">
              {['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'].map((c) => (
                <button
                  key={c}
                  onClick={() => setColor(c)}
                  className={`w-6 h-6 rounded-full border-2 transition-transform ${
                    color === c ? 'border-white scale-110 shadow' : 'border-transparent'
                  }`}
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>
          </div>

          {/* Convert Rectangle button */}
          {type === 'rectangle' && (
            <button
              onClick={handleConvertToPolygon}
              className="w-full py-1.5 bg-gray-800 hover:bg-gray-700 text-sky-400 border border-gray-700 rounded-lg text-xs font-semibold transition"
            >
              Convert to Free Polygon
            </button>
          )}

          {/* Tripwire Line direction controls */}
          {type === 'line' && (
            <div className="space-y-2">
              <label className="block text-gray-400 font-semibold">Line Direction:</label>
              <select
                value={direction}
                onChange={(e) => setDirection(e.target.value)}
                className="w-full p-2 bg-gray-900 border border-gray-700 rounded-lg text-white"
              >
                <option value="both">Bidirectional (Both)</option>
                <option value="left_to_right">Left to Right</option>
                <option value="right_to_left">Right to Left</option>
              </select>
              <button
                onClick={handleFlipDirection}
                className="w-full py-1.5 bg-gray-800 hover:bg-gray-700 text-indigo-400 border border-gray-700 rounded-lg text-xs font-semibold transition flex items-center justify-center gap-1.5"
              >
                <ArrowRightLeft size={14} />
                Flip Line Direction
              </button>
            </div>
          )}

          {/* Target Classes */}
          <div>
            <label className="block text-gray-400 font-semibold mb-1.5">Target Classes:</label>
            <div className="grid grid-cols-2 gap-2">
              {['person', 'vehicle', 'animal', 'object'].map((cls) => (
                <label key={cls} className="flex items-center gap-2 cursor-pointer text-gray-300">
                  <input
                    type="checkbox"
                    checked={classes.includes(cls)}
                    onChange={(e) => {
                      if (e.target.checked) setClasses([...classes, cls]);
                      else setClasses(classes.filter((c) => c !== cls));
                    }}
                    className="rounded border-gray-700 bg-gray-900 text-indigo-600 focus:ring-0"
                  />
                  <span className="capitalize">{cls}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Enabled Switch */}
          <div className="flex items-center justify-between pt-2 border-t border-gray-800">
            <span className="text-gray-300 font-semibold">Enable Zone:</span>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600"></div>
            </label>
          </div>

          {/* Active Camera Zones List */}
          <div className="pt-3 border-t border-gray-800 flex-1 flex flex-col min-h-0">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-300 font-semibold">Camera Zones:</span>
              <button
                onClick={startNewZone}
                className="text-[10px] text-sky-400 hover:text-sky-300 font-semibold"
              >
                + New Zone
              </button>
            </div>
            <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
              {cameraZones.length === 0 ? (
                <p className="text-gray-500 italic text-[11px]">No zones for this camera yet.</p>
              ) : (
                cameraZones.map((z) => (
                  <div
                    key={z.id}
                    className={`p-2 rounded-lg border transition flex items-center justify-between ${
                      activeZoneId === z.id
                        ? 'bg-indigo-950/40 border-indigo-500/50'
                        : 'bg-gray-900 border-gray-800 hover:border-gray-700'
                    }`}
                  >
                    <div className="truncate min-w-0 pr-2">
                      <p className="font-semibold text-white truncate">{z.name}</p>
                      <p className="text-[10px] text-gray-400 capitalize">
                        {z.type || 'polygon'} • {z.classes?.join(', ')}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        onClick={() => loadZoneIntoEditor(z)}
                        className="p-1 text-sky-400 hover:bg-sky-950/50 rounded"
                        title="Edit Zone"
                      >
                        <Edit3 size={13} />
                      </button>
                      <button
                        onClick={async () => {
                          try {
                            const res = await fetch(`/api/zones/${z.id}`, { method: 'DELETE' });
                            if (res.ok) {
                              fetchCameraZones();
                              if (activeZoneId === z.id) startNewZone();
                            }
                          } catch (e) {}
                        }}
                        className="p-1 text-rose-400 hover:bg-rose-950/50 rounded"
                        title="Delete Zone"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Keyboard hints */}
          <div className="pt-2 border-t border-gray-800 text-[10px] text-gray-500 space-y-0.5 shrink-0">
            <p className="font-semibold text-gray-400">Shortcuts:</p>
            <p>• Click vertex + Del / Right-click to delete point</p>
            <p>• Arrow keys: nudge selected point by 1px (Shift=10px)</p>
            <p>• Ctrl+Z / Ctrl+Y: Undo / Redo</p>
          </div>
        </div>
      </div>
    </div>
  );
}
