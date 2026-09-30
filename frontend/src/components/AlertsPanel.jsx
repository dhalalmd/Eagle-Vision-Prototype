import React from 'react';
import { BellOff, ShieldAlert } from 'lucide-react';

export default function AlertsPanel() {
  return (
    <aside className="w-80 bg-[#111827] border-l border-gray-800 flex flex-col shrink-0">
      <div className="p-4 border-b border-gray-800 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-white font-semibold text-sm">
          <ShieldAlert size={18} className="text-amber-500" />
          <span>Real-time Alerts</span>
        </div>
        <span className="text-[11px] bg-gray-800 text-gray-400 px-2 py-0.5 rounded border border-gray-700">
          M07 Engine
        </span>
      </div>

      <div className="flex-1 p-6 flex flex-col items-center justify-center text-center text-gray-500">
        <BellOff size={32} className="mb-3 text-gray-600 stroke-[1.5]" />
        <p className="text-xs font-medium text-gray-400">No Active Security Alerts</p>
        <p className="text-[11px] text-gray-600 mt-1 max-w-[200px]">
          Detection & alert modules will populate real-time events here once enabled.
        </p>
      </div>
    </aside>
  );
}
