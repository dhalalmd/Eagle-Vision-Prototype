import React from 'react';
import { Video, Camera, Bell, Cpu, Settings, ShieldAlert } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'live', label: 'Live Grid', icon: Video },
    { id: 'cameras', label: 'Cameras', icon: Camera },
    { id: 'events', label: 'Events Feed', icon: Bell, placeholder: true },
    { id: 'modules', label: 'AI Modules', icon: Cpu, placeholder: true },
    { id: 'settings', label: 'Settings', icon: Settings, placeholder: true },
  ];

  return (
    <aside className="w-64 bg-[#111827] border-r border-gray-800 flex flex-col justify-between shrink-0">
      <div>
        <div className="p-5 flex items-center space-x-3 border-b border-gray-800">
          <div className="bg-sky-600 p-2 rounded-lg text-white">
            <ShieldAlert size={24} />
          </div>
          <div>
            <h1 className="font-bold text-white tracking-wide text-sm">SMART BORDER</h1>
            <p className="text-xs text-sky-400 font-medium">CCTV MONITORING</p>
          </div>
        </div>

        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-sky-600/20 text-sky-400 border border-sky-500/30'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon size={18} />
                  <span>{item.label}</span>
                </div>
                {item.placeholder && (
                  <span className="text-[10px] bg-gray-800 text-gray-500 px-1.5 py-0.5 rounded border border-gray-700">
                    M08+
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-gray-800 text-xs text-gray-500 text-center">
        SIH26187 Prototype v1.0
      </div>
    </aside>
  );
}
