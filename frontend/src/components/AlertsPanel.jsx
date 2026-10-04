import React, { useState, useEffect, useRef } from 'react';
import { ShieldAlert, Volume2, VolumeX, ExternalLink, Bell } from 'lucide-react';

function getRelativeTime(timestamp) {
  if (!timestamp) return '';
  const now = Date.now() / 1000;
  const diff = Math.max(0, Math.floor(now - timestamp));

  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function playBeepSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, ctx.currentTime); // A5 note
    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + 0.3);
  } catch (e) {
    // Audio Context not allowed until user interaction
  }
}

export default function AlertsPanel({ activeTab, setActiveTab, onSelectAlert, alerts, setAlerts, onNewAlertCamera }) {
  const [soundEnabled, setSoundEnabled] = useState(true);
  const soundRef = useRef(soundEnabled);
  soundRef.current = soundEnabled;

  // Poll stats for unread count
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchUnread = () => {
    fetch('/api/alerts/stats')
      .then((res) => res.json())
      .then((data) => setUnreadCount(data.unread || 0))
      .catch(() => {});
  };

  useEffect(() => {
    fetchUnread();
    const interval = setInterval(fetchUnread, 3000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket connection to /ws/alerts
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/alerts`;
    let ws = null;
    let reconnectTimeout = null;

    function connectWs() {
      try {
        ws = new WebSocket(wsUrl);

        ws.onmessage = (evt) => {
          try {
            const newAlert = JSON.parse(evt.data);
            if (newAlert && newAlert.id) {
              setAlerts((prev) => {
                if (prev.some((a) => a.id === newAlert.id)) return prev;
                return [newAlert, ...prev].slice(0, 50);
              });

              setUnreadCount((c) => c + 1);

              if (soundRef.current) {
                playBeepSound();
              }

              if (onNewAlertCamera && newAlert.camera_id) {
                onNewAlertCamera(newAlert.camera_id);
              }
            }
          } catch (e) {
            console.error('Failed to parse ws alert message', e);
          }
        };

        ws.onclose = () => {
          reconnectTimeout = setTimeout(connectWs, 3000);
        };
      } catch (err) {
        reconnectTimeout = setTimeout(connectWs, 5000);
      }
    }

    connectWs();
    return () => {
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, [setAlerts, onNewAlertCamera]);

  const severityDot = (sev) => {
    const s = String(sev).toLowerCase();
    if (s === 'critical') return 'bg-rose-500 shadow-rose-500/50 shadow-sm';
    if (s === 'high') return 'bg-orange-500 shadow-orange-500/50 shadow-sm';
    if (s === 'medium') return 'bg-amber-400';
    return 'bg-sky-400';
  };

  return (
    <aside className="w-80 bg-[#111827] border-l border-gray-800 flex flex-col shrink-0 h-full">
      {/* Panel Header */}
      <div className="p-3.5 border-b border-gray-800 flex items-center justify-between bg-gray-900/60">
        <div className="flex items-center space-x-2 text-white font-semibold text-xs tracking-wide">
          <ShieldAlert size={16} className="text-rose-500" />
          <span>REAL-TIME ALERTS</span>
          {unreadCount > 0 && (
            <span className="bg-rose-500 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full animate-pulse">
              {unreadCount}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setSoundEnabled(!soundEnabled)}
            className={`p-1 rounded transition-colors ${
              soundEnabled ? 'text-sky-400 hover:bg-sky-950/40' : 'text-gray-600 hover:text-gray-400'
            }`}
            title={soundEnabled ? 'Alert Sound ON' : 'Alert Sound MUTE'}
          >
            {soundEnabled ? <Volume2 size={15} /> : <VolumeX size={15} />}
          </button>

          <button
            onClick={() => setActiveTab('events')}
            className="flex items-center space-x-1 text-[11px] font-medium text-sky-400 hover:text-sky-300 transition-colors"
            title="View All Alerts"
          >
            <span>View all</span>
            <ExternalLink size={12} />
          </button>
        </div>
      </div>

      {/* Alerts Feed */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center text-gray-500">
            <Bell size={28} className="mb-2 text-gray-700 stroke-[1.5]" />
            <p className="text-xs font-medium text-gray-400">No Recent Alerts</p>
            <p className="text-[11px] text-gray-600 mt-1 max-w-[180px]">
              Intrusion & pipeline security alerts will appear here in real-time.
            </p>
          </div>
        ) : (
          alerts.slice(0, 20).map((alert) => (
            <div
              key={alert.id}
              onClick={() => {
                if (onSelectAlert) onSelectAlert(alert);
                setActiveTab('events');
              }}
              className={`p-2.5 rounded-lg border transition-all cursor-pointer text-left ${
                alert.status === 'new'
                  ? 'bg-[#151c2d] border-rose-500/40 hover:border-rose-500/80 shadow-md'
                  : 'bg-gray-900/60 border-gray-800 hover:border-gray-700 opacity-80'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center space-x-1.5 truncate">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${severityDot(alert.severity)}`} />
                  <span className="text-[11px] font-bold text-white truncate">
                    {alert.title || alert.type}
                  </span>
                </div>
                <span className="text-[10px] text-gray-500 shrink-0 font-mono">
                  {getRelativeTime(alert.timestamp)}
                </span>
              </div>

              <p className="text-[11px] text-gray-300 leading-tight line-clamp-2">{alert.message}</p>

              <div className="mt-1.5 flex items-center justify-between text-[10px] text-gray-500 border-t border-gray-800/60 pt-1">
                <span className="font-mono text-gray-400">{alert.camera_id}</span>
                <span
                  className={`capitalize px-1.5 py-0.2 rounded ${
                    alert.status === 'new'
                      ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      : alert.status === 'ack'
                      ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                      : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  }`}
                >
                  {alert.status}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
