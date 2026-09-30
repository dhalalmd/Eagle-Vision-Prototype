import React, { useState } from 'react';
import { Plus, Trash2, Edit2, QrCode, Power, Camera, Smartphone, Link as LinkIcon, FileVideo } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';

export default function CamerasPage({ cameras, onAddClick, onToggle, onDelete, onUpdate, systemInfo }) {
  const [editingCam, setEditingCam] = useState(null);
  const [qrModalCam, setQrModalCam] = useState(null);

  const getIcon = (type) => {
    switch (type) {
      case 'webcam': return Camera;
      case 'phone': return Smartphone;
      case 'url': return LinkIcon;
      case 'file': return FileVideo;
      default: return Camera;
    }
  };

  const lanIp = systemInfo?.lan_ip || window.location.hostname;

  return (
    <div className="p-6 flex-1 flex flex-col overflow-y-auto">
      <div className="flex items-center justify-between mb-6 shrink-0">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Camera Device Management</h2>
          <p className="text-xs text-gray-400">Add, edit, enable or remove surveillance sources dynamically</p>
        </div>

        <button
          onClick={onAddClick}
          className="bg-sky-600 hover:bg-sky-500 text-white px-4 py-2 rounded-lg text-xs font-semibold flex items-center space-x-2 transition-colors shadow-lg shadow-sky-900/30"
        >
          <Plus size={16} />
          <span>Add Camera Source</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cameras.map((cam) => {
          const Icon = getIcon(cam.type);
          const isPhone = cam.type === 'phone';
          const phoneUrl = `https://${lanIp}:8443/phone?cam=${cam.id}`;

          return (
            <div
              key={cam.id}
              className={`bg-[#111827] border rounded-xl p-5 flex flex-col justify-between transition-all ${
                cam.enabled ? 'border-gray-800' : 'border-gray-800/40 opacity-70'
              }`}
            >
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="p-2.5 bg-gray-800 rounded-lg text-sky-400">
                      <Icon size={20} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white text-sm">{cam.name}</h3>
                      <span className="text-[11px] text-gray-500 font-mono">
                        {cam.id} &bull; {cam.type.toUpperCase()}
                      </span>
                    </div>
                  </div>

                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                      cam.status === 'online'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : cam.status === 'connecting'
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                    }`}
                  >
                    {cam.status}
                  </span>
                </div>

                <div className="space-y-1 text-xs text-gray-400 mb-4 bg-gray-900/50 p-2.5 rounded-lg border border-gray-800/50">
                  <div className="flex justify-between">
                    <span>Source:</span>
                    <span className="font-mono text-gray-300 truncate max-w-[180px]">
                      {cam.source || '(Stream Push)'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>FPS:</span>
                    <span className="font-mono text-gray-300">{cam.fps}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-gray-800/80">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => onToggle(cam.id, !cam.enabled)}
                    className={`p-1.5 rounded-lg border transition-colors ${
                      cam.enabled
                        ? 'bg-emerald-600/20 border-emerald-500/40 text-emerald-400 hover:bg-emerald-600/30'
                        : 'bg-gray-800 border-gray-700 text-gray-500 hover:text-gray-300'
                    }`}
                    title={cam.enabled ? 'Disable Camera' : 'Enable Camera'}
                  >
                    <Power size={16} />
                  </button>

                  {isPhone && (
                    <button
                      onClick={() => setQrModalCam(cam)}
                      className="p-1.5 bg-gray-800 border border-gray-700 text-sky-400 rounded-lg hover:bg-gray-700"
                      title="Show QR Code for Phone"
                    >
                      <QrCode size={16} />
                    </button>
                  )}
                </div>

                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => {
                      const newName = prompt('Edit camera name:', cam.name);
                      if (newName && newName !== cam.name) {
                        onUpdate(cam.id, { name: newName });
                      }
                    }}
                    className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800"
                  >
                    <Edit2 size={16} />
                  </button>

                  <button
                    onClick={() => {
                      if (confirm(`Are you sure you want to delete camera ${cam.name}?`)) {
                        onDelete(cam.id);
                      }
                    }}
                    className="p-1.5 text-rose-400 hover:text-rose-300 rounded-lg hover:bg-rose-950/40"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* QR Code Modal */}
      {qrModalCam && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111827] border border-gray-800 rounded-xl p-6 max-w-sm w-full text-center relative">
            <h3 className="font-bold text-white text-base mb-2">Phone Connect QR Code</h3>
            <p className="text-xs text-gray-400 mb-4">{qrModalCam.name} ({qrModalCam.id})</p>

            <div className="bg-white p-4 rounded-xl inline-block mb-4">
              <QRCodeSVG value={`https://${lanIp}:8443/phone?cam=${qrModalCam.id}`} size={180} />
            </div>

            <div className="bg-gray-900 p-2 rounded border border-gray-800 text-[11px] text-sky-400 break-all select-all font-mono mb-4">
              https://{lanIp}:8443/phone?cam={qrModalCam.id}
            </div>

            <button
              onClick={() => setQrModalCam(null)}
              className="w-full bg-gray-800 hover:bg-gray-700 text-white py-2 rounded-lg text-xs font-semibold"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
