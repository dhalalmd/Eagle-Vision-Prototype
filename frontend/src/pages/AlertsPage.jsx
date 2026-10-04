import React, { useState, useEffect } from 'react';
import {
  ShieldAlert, Search, Filter, Download, CheckCircle, Clock,
  AlertTriangle, X, Save, RefreshCw, FileText, Check
} from 'lucide-react';

function formatDate(ts) {
  if (!ts) return '';
  return new Date(ts * 1000).toLocaleString();
}

export default function AlertsPage({ cameras, selectedAlert, setSelectedAlert }) {
  const [alerts, setAlerts] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [stats, setStats] = useState({ total: 0, unread: 0, by_severity: {}, by_status: {} });
  const [loading, setLoading] = useState(true);

  // Filters
  const [cameraId, setCameraId] = useState('all');
  const [type, setType] = useState('all');
  const [severity, setSeverity] = useState('all');
  const [status, setStatus] = useState('all');
  const [q, setQ] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [page, setPage] = useState(0);
  const limit = 20;

  // Drawer detail state
  const [activeAlert, setActiveAlert] = useState(selectedAlert || null);
  const [remarksText, setRemarksText] = useState('');
  const [savingRemarks, setSavingRemarks] = useState(false);

  useEffect(() => {
    if (selectedAlert) {
      setActiveAlert(selectedAlert);
      setRemarksText(selectedAlert.remarks || '');
    }
  }, [selectedAlert]);

  const fetchStats = () => {
    fetch('/api/alerts/stats')
      .then((res) => res.json())
      .then((data) => setStats(data))
      .catch(() => {});
  };

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (cameraId && cameraId !== 'all') params.append('camera_id', cameraId);
      if (type && type !== 'all') params.append('type', type);
      if (severity && severity !== 'all') params.append('severity', severity);
      if (status && status !== 'all') params.append('status', status);
      if (q) params.append('q', q);
      if (dateFrom) params.append('date_from', new Date(dateFrom).getTime() / 1000);
      if (dateTo) params.append('date_to', new Date(dateTo).getTime() / 1000 + 86399);

      params.append('limit', limit);
      params.append('offset', page * limit);

      const res = await fetch(`/api/alerts?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setAlerts(data.items || []);
        setTotalCount(data.total || 0);
      }
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchAlerts();
  }, [cameraId, type, severity, status, q, dateFrom, dateTo, page]);

  const handleExportCSV = () => {
    const params = new URLSearchParams();
    if (cameraId && cameraId !== 'all') params.append('camera_id', cameraId);
    if (type && type !== 'all') params.append('type', type);
    if (severity && severity !== 'all') params.append('severity', severity);
    if (status && status !== 'all') params.append('status', status);
    if (q) params.append('q', q);
    if (dateFrom) params.append('date_from', new Date(dateFrom).getTime() / 1000);
    if (dateTo) params.append('date_to', new Date(dateTo).getTime() / 1000 + 86399);

    window.open(`/api/alerts/export.csv?${params.toString()}`, '_blank');
  };

  const handleUpdateStatus = async (alertId, newStatus) => {
    try {
      const res = await fetch(`/api/alerts/${alertId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        const updated = await res.json();
        setAlerts((prev) => prev.map((a) => (a.id === alertId ? updated : a)));
        if (activeAlert && activeAlert.id === alertId) {
          setActiveAlert(updated);
        }
        fetchStats();
      }
    } catch (err) {
      console.error('Failed to update alert status:', err);
    }
  };

  const handleSaveRemarks = async () => {
    if (!activeAlert) return;
    setSavingRemarks(true);
    try {
      const res = await fetch(`/api/alerts/${activeAlert.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ remarks: remarksText }),
      });
      if (res.ok) {
        const updated = await res.json();
        setActiveAlert(updated);
        setAlerts((prev) => prev.map((a) => (a.id === updated.id ? updated : a)));
      }
    } catch (err) {
      console.error('Failed to save remarks:', err);
    } finally {
      setSavingRemarks(false);
    }
  };

  const resetFilters = () => {
    setCameraId('all');
    setType('all');
    setSeverity('all');
    setStatus('all');
    setQ('');
    setDateFrom('');
    setDateTo('');
    setPage(0);
  };

  const totalPages = Math.max(1, Math.ceil(totalCount / limit));

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0b0f19] text-gray-100 overflow-hidden">
      {/* Header & Stats Cards */}
      <div className="p-6 border-b border-gray-800 shrink-0 bg-[#0f1420]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2 tracking-tight">
              <ShieldAlert className="w-7 h-7 text-rose-500" />
              Incident Alerts Log
            </h1>
            <p className="text-sm text-gray-400 mt-0.5">
              Comprehensive real-time incident records, audit logs, and response management.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleExportCSV}
              className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg text-sm border border-gray-700 transition"
            >
              <Download className="w-4 h-4 text-emerald-400" />
              Export CSV
            </button>
            <button
              onClick={() => { fetchStats(); fetchAlerts(); }}
              className="p-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg border border-gray-700 transition"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-[#141b2b] p-3 rounded-lg border border-gray-800 flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400 font-medium">Total Alerts</p>
              <p className="text-xl font-bold text-white mt-0.5">{stats.total || 0}</p>
            </div>
            <FileText className="w-6 h-6 text-indigo-400 opacity-60" />
          </div>

          <div className="bg-[#141b2b] p-3 rounded-lg border border-gray-800 flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400 font-medium">Unread / New</p>
              <p className="text-xl font-bold text-amber-400 mt-0.5">{stats.unread || 0}</p>
            </div>
            <Clock className="w-6 h-6 text-amber-400 opacity-60" />
          </div>

          <div className="bg-[#141b2b] p-3 rounded-lg border border-gray-800 flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400 font-medium">High / Critical</p>
              <p className="text-xl font-bold text-rose-400 mt-0.5">
                {(stats.by_severity?.high || 0) + (stats.by_severity?.critical || 0)}
              </p>
            </div>
            <AlertTriangle className="w-6 h-6 text-rose-400 opacity-60" />
          </div>

          <div className="bg-[#141b2b] p-3 rounded-lg border border-gray-800 flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400 font-medium">Resolved / Ack</p>
              <p className="text-xl font-bold text-emerald-400 mt-0.5">
                {(stats.by_status?.resolved || 0) + (stats.by_status?.ack || 0)}
              </p>
            </div>
            <CheckCircle className="w-6 h-6 text-emerald-400 opacity-60" />
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="px-6 py-3 bg-[#111624] border-b border-gray-800 flex flex-wrap items-center gap-3 shrink-0 text-xs">
        {/* Search */}
        <div className="relative flex-1 min-w-[180px]">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-gray-500" />
          <input
            type="text"
            placeholder="Search message, title, remarks..."
            value={q}
            onChange={(e) => { setQ(e.target.value); setPage(0); }}
            className="w-full pl-8 pr-3 py-1.5 bg-gray-900 border border-gray-700 rounded-md text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        {/* Camera */}
        <select
          value={cameraId}
          onChange={(e) => { setCameraId(e.target.value); setPage(0); }}
          className="bg-gray-900 border border-gray-700 rounded-md px-2.5 py-1.5 text-gray-200"
        >
          <option value="all">All Cameras</option>
          {cameras.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name} ({c.id})
            </option>
          ))}
        </select>

        {/* Severity */}
        <select
          value={severity}
          onChange={(e) => { setSeverity(e.target.value); setPage(0); }}
          className="bg-gray-900 border border-gray-700 rounded-md px-2.5 py-1.5 text-gray-200"
        >
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        {/* Status */}
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(0); }}
          className="bg-gray-900 border border-gray-700 rounded-md px-2.5 py-1.5 text-gray-200"
        >
          <option value="all">All Statuses</option>
          <option value="new">New</option>
          <option value="ack">Acknowledged</option>
          <option value="resolved">Resolved</option>
        </select>

        {/* Date From */}
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => { setDateFrom(e.target.value); setPage(0); }}
          className="bg-gray-900 border border-gray-700 rounded-md px-2 py-1 text-gray-200"
        />

        {/* Date To */}
        <input
          type="date"
          value={dateTo}
          onChange={(e) => { setDateTo(e.target.value); setPage(0); }}
          className="bg-gray-900 border border-gray-700 rounded-md px-2 py-1 text-gray-200"
        />

        <button
          onClick={resetFilters}
          className="px-2.5 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded-md transition"
        >
          Reset
        </button>
      </div>

      {/* Main Table Content */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-20 text-gray-500">
              <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading alerts...
            </div>
          ) : alerts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-gray-500">
              <ShieldAlert className="w-10 h-10 mb-2 text-gray-700 stroke-[1.5]" />
              <p className="text-sm font-semibold text-gray-400">No Alerts Found</p>
              <p className="text-xs text-gray-600 mt-1">Adjust your filters or trigger new security events.</p>
            </div>
          ) : (
            <div className="bg-[#121826] border border-gray-800 rounded-xl overflow-hidden shadow-lg">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-gray-900/90 text-gray-400 border-b border-gray-800 font-semibold uppercase tracking-wider">
                    <th className="py-3 px-4">Time</th>
                    <th className="py-3 px-4">Camera</th>
                    <th className="py-3 px-4">Severity</th>
                    <th className="py-3 px-4">Title / Message</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Remarks</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/60">
                  {alerts.map((alert) => {
                    const isSelected = activeAlert && activeAlert.id === alert.id;

                    return (
                      <tr
                        key={alert.id}
                        onClick={() => {
                          setActiveAlert(alert);
                          setRemarksText(alert.remarks || '');
                        }}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-indigo-950/40 text-white'
                            : 'hover:bg-gray-800/40 text-gray-300'
                        }`}
                      >
                        <td className="py-3 px-4 font-mono text-gray-400 whitespace-nowrap">
                          {formatDate(alert.timestamp)}
                        </td>
                        <td className="py-3 px-4 font-medium text-white whitespace-nowrap">
                          {alert.camera_id}
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                              alert.severity === 'critical'
                                ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                                : alert.severity === 'high'
                                ? 'bg-orange-500/10 text-orange-400 border border-orange-500/30'
                                : alert.severity === 'medium'
                                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                                : 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
                            }`}
                          >
                            {alert.severity}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <p className="font-semibold text-white">{alert.title}</p>
                          <p className="text-gray-400 text-[11px] mt-0.5 line-clamp-1">{alert.message}</p>
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span
                            className={`capitalize px-2 py-0.5 rounded text-[11px] font-medium ${
                              alert.status === 'new'
                                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                                : alert.status === 'ack'
                                ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
                                : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            }`}
                          >
                            {alert.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-gray-400 italic max-w-[150px] truncate">
                          {alert.remarks || '-'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {/* Pagination Footer */}
              <div className="px-4 py-3 bg-gray-900/60 border-t border-gray-800 flex items-center justify-between text-xs text-gray-400">
                <span>
                  Showing {page * limit + 1}–{Math.min(totalCount, (page + 1) * limit)} of {totalCount}
                </span>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(Math.max(0, page - 1))}
                    disabled={page === 0}
                    className="px-2.5 py-1 bg-gray-800 rounded hover:bg-gray-700 disabled:opacity-30"
                  >
                    Previous
                  </button>
                  <span>
                    {page + 1} / {totalPages}
                  </span>
                  <button
                    onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                    disabled={page >= totalPages - 1}
                    className="px-2.5 py-1 bg-gray-800 rounded hover:bg-gray-700 disabled:opacity-30"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Detail Drawer */}
        {activeAlert && (
          <div className="w-96 bg-[#101625] border-l border-gray-800 flex flex-col shrink-0 h-full p-5 overflow-y-auto">
            <div className="flex items-start justify-between border-b border-gray-800 pb-3">
              <div>
                <span className="text-[10px] font-mono text-gray-400 uppercase">Alert #{activeAlert.id}</span>
                <h3 className="text-base font-bold text-white mt-0.5">{activeAlert.title}</h3>
              </div>
              <button
                onClick={() => setActiveAlert(null)}
                className="text-gray-400 hover:text-white p-1 rounded-md hover:bg-gray-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4 text-xs">
              {/* Severity & Status badges */}
              <div className="flex items-center justify-between">
                <span
                  className={`px-2.5 py-1 rounded text-xs font-bold uppercase ${
                    activeAlert.severity === 'high'
                      ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                      : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                  }`}
                >
                  {activeAlert.severity} Severity
                </span>
                <span className="capitalize text-gray-300 bg-gray-800 px-2 py-1 rounded border border-gray-700">
                  Status: {activeAlert.status}
                </span>
              </div>

              {/* Info grid */}
              <div className="bg-[#141b2a] p-3 rounded-lg border border-gray-800 space-y-2">
                <div>
                  <span className="text-gray-400 block text-[11px]">Camera ID:</span>
                  <span className="font-semibold text-white">{activeAlert.camera_id}</span>
                </div>
                <div>
                  <span className="text-gray-400 block text-[11px]">Timestamp:</span>
                  <span className="font-mono text-gray-200">{formatDate(activeAlert.timestamp)}</span>
                </div>
                <div>
                  <span className="text-gray-400 block text-[11px]">Full Message:</span>
                  <p className="text-gray-200 leading-relaxed mt-0.5">{activeAlert.message}</p>
                </div>
              </div>

              {/* Status Action Buttons */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleUpdateStatus(activeAlert.id, 'ack')}
                  disabled={activeAlert.status === 'ack'}
                  className="flex-1 py-1.5 px-3 bg-sky-600/20 hover:bg-sky-600/30 text-sky-400 border border-sky-500/30 rounded-lg font-medium transition disabled:opacity-40"
                >
                  Acknowledge
                </button>
                <button
                  onClick={() => handleUpdateStatus(activeAlert.id, 'resolved')}
                  disabled={activeAlert.status === 'resolved'}
                  className="flex-1 py-1.5 px-3 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 rounded-lg font-medium transition disabled:opacity-40"
                >
                  Resolve
                </button>
              </div>

              {/* Remarks Section */}
              <div className="pt-2">
                <label className="block text-xs font-semibold text-gray-300 mb-1">
                  Operator Remarks:
                </label>
                <textarea
                  rows={3}
                  value={remarksText}
                  onChange={(e) => setRemarksText(e.target.value)}
                  placeholder="Enter notes or resolution remarks..."
                  className="w-full p-2.5 bg-gray-900 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                />
                <button
                  onClick={handleSaveRemarks}
                  disabled={savingRemarks}
                  className="mt-2 w-full flex items-center justify-center gap-1.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium transition"
                >
                  <Save className="w-4 h-4" />
                  {savingRemarks ? 'Saving...' : 'Save Remarks'}
                </button>
              </div>

              {/* Evidence Section */}
              {activeAlert.evidence_path ? (
                <div className="pt-2">
                  <span className="block text-xs font-semibold text-gray-300 mb-1">
                    Event Snapshot Evidence:
                  </span>
                  <img
                    src={`/api/evidence/${activeAlert.evidence_path}`}
                    alt="Evidence"
                    className="w-full rounded-lg border border-gray-700 object-cover"
                  />
                </div>
              ) : (
                <p className="text-[11px] text-gray-500 italic pt-2">
                  No snapshot evidence attached (evidence module handles clips/snapshots).
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
