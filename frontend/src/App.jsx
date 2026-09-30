import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import AlertsPanel from './components/AlertsPanel';
import AddCameraModal from './components/AddCameraModal';
import LiveViewPage from './pages/LiveViewPage';
import CamerasPage from './pages/CamerasPage';
import PlaceholderPage from './pages/PlaceholderPage';

export default function App() {
  const [activeTab, setActiveTab] = useState('live');
  const [cameras, setCameras] = useState([]);
  const [systemInfo, setSystemInfo] = useState(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // Poll cameras every 2 seconds per M08 spec
  useEffect(() => {
    const fetchCameras = () => {
      fetch('/api/cameras')
        .then((res) => res.json())
        .then((data) => setCameras(data))
        .catch(() => {});
    };

    fetchCameras();
    const interval = setInterval(fetchCameras, 2000);
    return () => clearInterval(interval);
  }, []);

  // Fetch system info
  useEffect(() => {
    fetch('/api/system/info')
      .then((res) => res.json())
      .then((data) => setSystemInfo(data))
      .catch(() => {});
  }, []);

  const handleAddCamera = async (newCam) => {
    try {
      const res = await fetch('/api/cameras', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newCam),
      });
      const data = await res.json();
      setCameras((prev) => [...prev, data]);
      return data;
    } catch (err) {
      console.error('Failed to add camera:', err);
      return null;
    }
  };

  const handleToggleCamera = async (id, enabled) => {
    try {
      const res = await fetch(`/api/cameras/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      });
      const updated = await res.json();
      setCameras((prev) => prev.map((c) => (c.id === id ? updated : c)));
    } catch (err) {
      console.error('Failed to toggle camera:', err);
    }
  };

  const handleUpdateCamera = async (id, payload) => {
    try {
      const res = await fetch(`/api/cameras/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const updated = await res.json();
      setCameras((prev) => prev.map((c) => (c.id === id ? updated : c)));
    } catch (err) {
      console.error('Failed to update camera:', err);
    }
  };

  const handleDeleteCamera = async (id) => {
    try {
      await fetch(`/api/cameras/${id}`, { method: 'DELETE' });
      setCameras((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      console.error('Failed to delete camera:', err);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0b0f19]">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className="flex-1 flex flex-col min-w-0">
        <TopBar cameras={cameras} />

        <div className="flex-1 flex overflow-hidden">
          <main className="flex-1 flex flex-col min-w-0 bg-[#0b0f19]">
            {activeTab === 'live' && <LiveViewPage cameras={cameras} />}
            {activeTab === 'cameras' && (
              <CamerasPage
                cameras={cameras}
                onAddClick={() => setIsAddModalOpen(true)}
                onToggle={handleToggleCamera}
                onDelete={handleDeleteCamera}
                onUpdate={handleUpdateCamera}
                systemInfo={systemInfo}
              />
            )}
            {activeTab === 'events' && <PlaceholderPage title="Events History" moduleCode="M04 / M07" />}
            {activeTab === 'modules' && <PlaceholderPage title="AI Module Toggles" moduleCode="M08 Phase 2" />}
            {activeTab === 'settings' && <PlaceholderPage title="System Settings" moduleCode="M18" />}
          </main>

          <AlertsPanel />
        </div>
      </div>

      <AddCameraModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAdd={handleAddCamera}
        systemInfo={systemInfo}
      />
    </div>
  );
}
