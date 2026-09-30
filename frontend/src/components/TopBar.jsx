import React, { useState, useEffect } from 'react';
import { Clock, Activity, Wifi } from 'lucide-react';

export default function TopBar({ cameras }) {
  const [timeStr, setTimeStr] = useState('');

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString() + ' - ' + now.toLocaleDateString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const totalCams = cameras.length;
  const onlineCams = cameras.filter((c) => c.status === 'online').length;

  return (
    <header className="h-16 bg-[#111827] border-b border-gray-800 px-6 flex items-center justify-between shrink-0">
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2 text-gray-300 text-sm font-medium">
          <Clock size={16} className="text-sky-400" />
          <span>{timeStr || 'Loading clock...'}</span>
        </div>
      </div>

      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2 bg-gray-800/80 px-3 py-1.5 rounded-full border border-gray-700 text-xs">
          <Wifi size={14} className={onlineCams > 0 ? 'text-emerald-400' : 'text-amber-400'} />
          <span className="text-gray-300 font-medium">
            Cameras Online: <strong className="text-white">{onlineCams}/{totalCams}</strong>
          </span>
        </div>

        <div className="flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1.5 rounded-full text-xs text-emerald-400 font-medium">
          <Activity size={14} />
          <span>System Healthy</span>
        </div>
      </div>
    </header>
  );
}
