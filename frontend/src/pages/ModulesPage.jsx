import React, { useState, useEffect } from 'react';
import { Cpu, CheckCircle2, XCircle, AlertTriangle, RefreshCw, Zap } from 'lucide-react';

export default function ModulesPage() {
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState({});

  const fetchModules = async () => {
    try {
      const res = await fetch('/api/modules');
      if (res.ok) {
        const data = await res.json();
        setModules(data);
      }
    } catch (err) {
      console.error('Failed to fetch modules:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModules();
    const interval = setInterval(fetchModules, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleToggle = async (name) => {
    setToggling((prev) => ({ ...prev, [name]: true }));
    try {
      const res = await fetch(`/api/modules/${name}/toggle`, {
        method: 'POST',
      });
      if (res.ok) {
        await fetchModules();
      }
    } catch (err) {
      console.error(`Failed to toggle module ${name}:`, err);
    } finally {
      setToggling((prev) => ({ ...prev, [name]: false }));
    }
  };

  const handleGroupCheckbox = async (group, isChecked, currentConfig) => {
    const allGroups = ['person', 'vehicle', 'animal', 'object'];
    let currentClasses = currentConfig?.classes || 'all';

    let activeGroups = [];
    if (currentClasses === 'all' || (Array.isArray(currentClasses) && currentClasses.includes('all'))) {
      activeGroups = [...allGroups];
    } else if (Array.isArray(currentClasses)) {
      activeGroups = currentClasses.map((c) => String(c).toLowerCase());
    } else {
      activeGroups = [...allGroups];
    }

    if (isChecked) {
      if (!activeGroups.includes(group)) {
        activeGroups.push(group);
      }
    } else {
      activeGroups = activeGroups.filter((g) => g !== group);
    }

    const updatedClasses = activeGroups.length === 4 ? 'all' : activeGroups;

    try {
      const res = await fetch('/api/modules/detection/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ classes: updatedClasses }),
      });
      if (res.ok) {
        await fetchModules();
      }
    } catch (err) {
      console.error('Failed to update detection classes:', err);
    }
  };

  const moduleDescriptions = {
    detection: 'YOLOv8 Object Detection for all 80 COCO classes grouped into person, vehicle, animal, and object.',
    tracking: 'ByteTrack Multi-Object Tracker assigning unique stable track IDs to detected objects.',
    intrusion: 'Shapely zone polygon boundary monitor triggering real-time intrusion events.',
    event_engine: 'Event deduplication, severity ranking, and rule filter engine.',
    evidence: 'Automatic snapshot and rolling video clip generator upon alert events.',
    database: 'SQL database logger storing persistent incident records.',
    alerts: 'WebSocket real-time broadcast service delivering alerts to live clients.',
    tamper: 'Camera tamper, blur, occlusion, and movement change detector.',
    night_enhance: 'Low-light Adaptive CLAHE and gamma image enhancer.',
    loitering: 'Dwell time monitoring for lingering targets inside restricted zones.',
    object_left: 'Abandoned object and left-behind package detection using frame subtraction.',
    anpr: 'Automatic License Plate Recognition via YOLO crop and OCR reader.',
    emergency_trigger: 'Emergency dispatch trigger simulation module.',
  };

  const groupsDef = [
    { key: 'person', label: 'Person', colorBg: 'bg-emerald-400' },
    { key: 'vehicle', label: 'Vehicle', colorBg: 'bg-amber-500' },
    { key: 'animal', label: 'Animal', colorBg: 'bg-yellow-400' },
    { key: 'object', label: 'Object', colorBg: 'bg-purple-500' },
  ];

  return (
    <div className="flex-1 p-6 overflow-y-auto bg-[#0b0f19] text-gray-100">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Cpu className="w-7 h-7 text-indigo-400" />
            AI Pipeline Modules
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Enable or disable computer vision pipeline modules at runtime without restarting servers.
          </p>
        </div>
        <button
          onClick={fetchModules}
          className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-md text-sm border border-gray-700 transition"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Status
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-gray-400">
          <RefreshCw className="w-6 h-6 animate-spin mr-2" /> Loading module states...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {modules.map((mod) => {
            const isEnabled = mod.enabled;
            const isToggling = toggling[mod.name];
            const desc = moduleDescriptions[mod.name] || 'Pipeline processing module.';

            return (
              <div
                key={mod.name}
                className={`p-5 rounded-xl border transition-all ${
                  isEnabled
                    ? 'bg-[#121927] border-indigo-500/40 shadow-lg shadow-indigo-950/20'
                    : 'bg-[#0f1420] border-gray-800 opacity-80'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-white capitalize flex items-center gap-2">
                      {mod.name.replace('_', ' ')}
                    </h2>
                    <div className="mt-1 flex items-center gap-2">
                      {mod.status === 'active' && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 className="w-3 h-3 mr-1" /> Active
                        </span>
                      )}
                      {mod.status === 'disabled' && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-500/10 text-gray-400 border border-gray-500/20">
                          <XCircle className="w-3 h-3 mr-1" /> Disabled
                        </span>
                      )}
                      {mod.status === 'failed' && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
                          <AlertTriangle className="w-3 h-3 mr-1" /> Failed ({mod.failures}/5)
                        </span>
                      )}

                      {mod.avg_ms != null && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                          <Zap className="w-3 h-3 mr-1 text-indigo-400" /> {mod.avg_ms} ms/frame
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Toggle Switch */}
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isEnabled}
                      disabled={isToggling}
                      onChange={() => handleToggle(mod.name)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                  </label>
                </div>

                <p className="mt-3 text-xs text-gray-400 leading-relaxed">{desc}</p>

                {/* Class Group Filter Checkboxes for Detection Module */}
                {mod.name === 'detection' && (
                  <div className="mt-4 pt-3 border-t border-gray-800/80">
                    <span className="text-xs font-medium text-gray-300 block mb-2">
                      Active Object Groups:
                    </span>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {groupsDef.map((grp) => {
                        const cfgClasses = mod.config?.classes || 'all';
                        const isChecked =
                          cfgClasses === 'all' ||
                          (Array.isArray(cfgClasses) &&
                            (cfgClasses.includes('all') ||
                              cfgClasses.map((c) => String(c).toLowerCase()).includes(grp.key)));

                        return (
                          <label
                            key={grp.key}
                            className="flex items-center gap-1.5 cursor-pointer text-gray-300 hover:text-white"
                          >
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={(e) =>
                                handleGroupCheckbox(grp.key, e.target.checked, mod.config)
                              }
                              className="rounded border-gray-700 bg-gray-900 text-indigo-600 focus:ring-0 focus:ring-offset-0 w-3.5 h-3.5"
                            />
                            <span className={`w-2 h-2 rounded-full ${grp.colorBg}`} />
                            <span className="capitalize">{grp.label}</span>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

