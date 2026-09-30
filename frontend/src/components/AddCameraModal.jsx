import React, { useState, useEffect } from 'react';
import { X, QrCode, Camera, Smartphone, Link as LinkIcon, FileVideo } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';

export default function AddCameraModal({ isOpen, onClose, onAdd, systemInfo }) {
  const [camType, setCamType] = useState('webcam');
  const [name, setName] = useState('');
  const [source, setSource] = useState('0');
  const [webcams, setWebcams] = useState([]);
  const [addedCam, setAddedCam] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetch('/api/webcams')
        .then((res) => res.json())
        .then((data) => setWebcams(data))
        .catch(() => setWebcams([]));
      setAddedCam(null);
      setName('');
      setSource('0');
      setCamType('webcam');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const finalName = name.trim() || `${camType.toUpperCase()} Camera`;
    const finalSource = camType === 'phone' ? '' : source;

    onAdd({ name: finalName, type: camType, source: finalSource, enabled: true }).then((newCam) => {
      if (camType === 'phone' && newCam) {
        setAddedCam(newCam);
      } else {
        onClose();
      }
    });
  };

  const lanIp = systemInfo?.lan_ip || window.location.hostname;
  const phoneUrl = `https://${lanIp}:8443/phone?cam=${addedCam?.id || 'cam_phone'}`;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#111827] border border-gray-800 rounded-xl w-full max-w-md p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white"
        >
          <X size={20} />
        </button>

        {!addedCam ? (
          <>
            <h2 className="text-lg font-bold text-white mb-4 flex items-center space-x-2">
              <Camera className="text-sky-400" size={22} />
              <span>Add New Camera</span>
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2">Camera Type</label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: 'webcam', label: 'Laptop Webcam', icon: Camera },
                    { id: 'phone', label: 'Phone Camera', icon: Smartphone },
                    { id: 'url', label: 'IP / RTSP Stream', icon: LinkIcon },
                    { id: 'file', label: 'Video File', icon: FileVideo },
                  ].map((t) => {
                    const Icon = t.icon;
                    return (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => {
                          setCamType(t.id);
                          if (t.id === 'webcam') setSource('0');
                          else if (t.id === 'url') setSource('rtsp://');
                          else if (t.id === 'file') setSource('data/samples/border.mp4');
                        }}
                        className={`flex items-center space-x-2 p-3 rounded-lg border text-xs font-medium text-left transition-colors ${
                          camType === t.id
                            ? 'bg-sky-600/20 border-sky-500 text-sky-300'
                            : 'bg-gray-800/50 border-gray-700 text-gray-400 hover:bg-gray-800'
                        }`}
                      >
                        <Icon size={16} />
                        <span>{t.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Camera Name</label>
                <input
                  type="text"
                  placeholder="e.g. North Gate Camera"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              {camType === 'webcam' && (
                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-1">Webcam Device</label>
                  <select
                    value={source}
                    onChange={(e) => setSource(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500"
                  >
                    {webcams.length > 0 ? (
                      webcams.map((w) => (
                        <option key={w.index} value={String(w.index)}>
                          Index {w.index} ({w.name})
                        </option>
                      ))
                    ) : (
                      <option value="0">Default Webcam (0)</option>
                    )}
                  </select>
                </div>
              )}

              {camType === 'url' && (
                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-1">RTSP / HTTP Stream URL</label>
                  <input
                    type="text"
                    value={source}
                    onChange={(e) => setSource(e.target.value)}
                    placeholder="rtsp://admin:pass@192.168.1.50:554/stream"
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500"
                    required
                  />
                </div>
              )}

              {camType === 'file' && (
                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-1">Video File Path</label>
                  <input
                    type="text"
                    value={source}
                    onChange={(e) => setSource(e.target.value)}
                    placeholder="data/samples/border.mp4"
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500"
                    required
                  />
                </div>
              )}

              {camType === 'phone' && (
                <div className="bg-sky-950/40 border border-sky-800/50 p-3 rounded-lg text-xs text-sky-300">
                  Phone camera will connect via WebRTC/WebSocket over HTTPS. A QR code will be generated upon saving.
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-3 border-t border-gray-800">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-xs font-medium text-gray-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-sky-600 hover:bg-sky-500 text-white px-5 py-2 rounded-lg text-xs font-semibold transition-colors"
                >
                  Save Camera
                </button>
              </div>
            </form>
          </>
        ) : (
          <div className="text-center py-2">
            <h3 className="text-base font-bold text-white mb-2 flex items-center justify-center space-x-2">
              <QrCode className="text-sky-400" size={20} />
              <span>Scan to Connect Phone</span>
            </h3>
            <p className="text-xs text-gray-400 mb-4">
              Scan with phone on the same Wi-Fi, then accept the self-signed certificate.
            </p>

            <div className="bg-white p-4 rounded-xl inline-block mb-4 shadow-inner">
              <QRCodeSVG value={phoneUrl} size={180} />
            </div>

            <div className="bg-gray-900 p-2.5 rounded-lg border border-gray-800 text-[11px] text-sky-400 break-all select-all font-mono mb-5">
              {phoneUrl}
            </div>

            <button
              onClick={onClose}
              className="w-full bg-sky-600 hover:bg-sky-500 text-white py-2.5 rounded-lg text-xs font-semibold"
            >
              Done & Open Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
