import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatInterface } from './components/ChatInterface';
import { StatusPanel } from './components/StatusPanel';
import { VoiceControl } from './components/VoiceControl';
import { apiFetch } from './hooks/useApi';
import type { SystemStatus, HealthStatus } from './types';

function App() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [activeTab, setActiveTab] = useState<'chat' | 'status' | 'voice'>('chat');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    apiFetch<HealthStatus>('/health').then(setHealth).catch(() => null);
    apiFetch<SystemStatus>('/system/status').then(setSystemStatus).catch(() => null);

    const interval = setInterval(() => {
      apiFetch<HealthStatus>('/health').then(setHealth).catch(() => null);
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-iron-950 text-iron-100">
      <Sidebar
        open={sidebarOpen}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />

      <div className="flex flex-1 flex-col min-w-0">
        <Header
          status={health?.status || 'unknown'}
          version={health?.version || '1.0.0'}
          onMenuToggle={() => setSidebarOpen(!sidebarOpen)}
        />

        <main className="flex-1 overflow-hidden relative">
          {activeTab === 'chat' && <ChatInterface />}
          {activeTab === 'status' && <StatusPanel systemStatus={systemStatus} health={health} />}
          {activeTab === 'voice' && <VoiceControl />}
        </main>
      </div>
    </div>
  );
}

export default App;
