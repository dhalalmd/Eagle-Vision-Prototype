import React, { useState, useEffect, useRef, useCallback } from 'react';
import { X, RotateCw, RefreshCcw } from 'lucide-react';

const DEFAULT_SETTINGS = {
  brightness: 0, contrast: 1.0, saturation: 1.0, zoom: 1.0,
  rotate: 0, flip_h: false, flip_v: false, grayscale: false, invert_colors: false,
};

export default function EditCameraModal({ camera, onClose, onUpdate }) {
  const [name, setName] = useState(camera.name);
  const [source, setSource] = useState(camera.source);
  const [settings, setSettings] = useState({ ...DEFAULT_SETTINGS, ...(camera.settings || {}) });
  const [saved, setSaved] = useState(false);
  const debounceRef = useRef(null);
  const initialSettingsRef = useRef({ ...DEFAULT_SETTINGS, ...(camera.settings || {}) });

  // Debounced PATCH for settings
  const patchSettings = useCallback((newSettings) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      onUpdate(camera.id, { settings: newSettings });
    }, 150);
  }, [camera.id, onUpdate]);

  const updateSetting = (key, value) => {
    const next = { ...settings, [key]: value };
    setSettings(next);
    patchSettings(next);
  };

  const handleReset = async () => {
    try {
      await fetch(`/api/cameras/${camera.id}/reset-settings`, { method: 'POST' });
      setSettings({ ...DEFAULT_SETTINGS });
      // Force refresh by patching with defaults
    } catch (e) { console.error(e); }
  };

  const handleSaveName = () => {
    if (name.trim() && name !== camera.name) {
      onUpdate(camera.id, { name: name.trim() });
    }
    if (source !== camera.source) {
      onUpdate(camera.id, { source });
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  };

  const handleCancel = () => {
    // Restore settings to what they were when the modal opened
    onUpdate(camera.id, { settings: initialSettingsRef.current });
    onClose();
  };

  const rotateValues = [0, 90, 180, 270];

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#111827] border border-gray-800 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-5 shadow-2xl relative">
        <button onClick={handleCancel} className="absolute top-4 right-4 text-gray-400 hover:text-white z-10">
          <X size={20} />
        </button>

        <h2 className="text-base font-bold text-white mb-4">Edit Camera — {camera.id}</h2>

        <div className="flex flex-col lg:flex-row gap-5">
          {/* Left: Live preview */}
          <div className="flex-1 min-w-0">
            <p className="text-[11px] text-gray-400 font-semibold uppercase tracking-wider mb-2">Live Preview</p>
            <div className="bg-black rounded-lg overflow-hidden aspect-video flex items-center justify-center border border-gray-800">
              {camera.status === 'online' ? (
                <img
                  src={`/api/stream/${camera.id}`}
                  alt="preview"
                  className="w-full h-full object-contain"
                />
              ) : (
                <span className="text-xs text-gray-600">Camera offline</span>
              )}
            </div>

            {/* Name + Source */}
            <div className="mt-4 space-y-3">
              <div>
                <label className="block text-[11px] text-gray-400 font-semibold mb-1">Name</label>
                <input
                  type="text" value={name} onChange={(e) => setName(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-sky-500"
                />
              </div>
              {camera.type !== 'phone' && (
                <div>
                  <label className="block text-[11px] text-gray-400 font-semibold mb-1">Source</label>
                  <input
                    type="text" value={source} onChange={(e) => setSource(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-sky-500"
                  />
                </div>
              )}
              <button onClick={handleSaveName}
                className="text-xs bg-sky-600 hover:bg-sky-500 text-white px-4 py-1.5 rounded-lg font-semibold transition-colors">
                {saved ? '✓ Saved' : 'Save Name/Source'}
              </button>
            </div>
          </div>

          {/* Right: Settings controls */}
          <div className="w-full lg:w-64 shrink-0 space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-[11px] text-gray-400 font-semibold uppercase tracking-wider">Image Settings</p>
              <button onClick={handleReset}
                className="flex items-center gap-1 text-[10px] text-amber-400 hover:text-amber-300 font-semibold">
                <RefreshCcw size={11} /> Reset
              </button>
            </div>

            {/* Brightness */}
            <SettingSlider label="Brightness" value={settings.brightness} min={-100} max={100} step={1}
              onChange={(v) => updateSetting('brightness', v)} display={v => v} />

            {/* Contrast */}
            <SettingSlider label="Contrast" value={settings.contrast} min={0.5} max={2.0} step={0.05}
              onChange={(v) => updateSetting('contrast', v)} display={v => v.toFixed(2)} />

            {/* Saturation */}
            <SettingSlider label="Saturation" value={settings.saturation} min={0.0} max={2.0} step={0.05}
              onChange={(v) => updateSetting('saturation', v)} display={v => v.toFixed(2)} />

            {/* Zoom */}
            <SettingSlider label="Zoom" value={settings.zoom} min={1.0} max={3.0} step={0.1}
              onChange={(v) => updateSetting('zoom', v)} display={v => v.toFixed(1) + 'x'} />

            {/* Rotate */}
            <div>
              <p className="text-[10px] text-gray-500 font-semibold mb-1.5">Rotate</p>
              <div className="flex gap-1.5">
                {rotateValues.map((r) => (
                  <button key={r} onClick={() => updateSetting('rotate', r)}
                    className={`flex-1 py-1 rounded text-[10px] font-bold transition-colors border ${
                      settings.rotate === r
                        ? 'bg-sky-600 border-sky-500 text-white'
                        : 'bg-gray-900 border-gray-700 text-gray-400 hover:bg-gray-800'
                    }`}>
                    {r}°
                  </button>
                ))}
              </div>
            </div>

            {/* Toggles */}
            <div className="space-y-2 pt-1">
              <Toggle label="Flip Horizontal" checked={settings.flip_h}
                onChange={(v) => updateSetting('flip_h', v)} />
              <Toggle label="Flip Vertical" checked={settings.flip_v}
                onChange={(v) => updateSetting('flip_v', v)} />
              <Toggle label="Grayscale" checked={settings.grayscale}
                onChange={(v) => updateSetting('grayscale', v)} />
              <Toggle label="Invert Colours" checked={settings.invert_colors}
                onChange={(v) => updateSetting('invert_colors', v)} />
            </div>

            <button onClick={onClose}
              className="w-full mt-3 bg-gray-800 hover:bg-gray-700 text-white py-2 rounded-lg text-xs font-semibold transition-colors">
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function SettingSlider({ label, value, min, max, step, onChange, display }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <p className="text-[10px] text-gray-500 font-semibold">{label}</p>
        <span className="text-[10px] text-gray-400 font-mono">{display(value)}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-1.5 bg-gray-700 rounded-full appearance-none cursor-pointer accent-sky-500"
      />
    </div>
  );
}

function Toggle({ label, checked, onChange }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[10px] text-gray-400">{label}</span>
      <button onClick={() => onChange(!checked)}
        className={`w-8 h-4.5 rounded-full relative transition-colors ${
          checked ? 'bg-sky-600' : 'bg-gray-700'
        }`} style={{ width: 32, height: 18 }}>
        <span className={`absolute top-0.5 w-3.5 h-3.5 rounded-full bg-white transition-transform ${
          checked ? 'left-[15px]' : 'left-0.5'
        }`} style={{ width: 14, height: 14 }} />
      </button>
    </div>
  );
}
