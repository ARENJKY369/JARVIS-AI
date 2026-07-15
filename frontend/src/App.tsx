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
  const [voice, setVoice] = useState<'jarvis' | 'friday'>('jarvis');

  useEffect(() => {
    apiFetch<HealthStatus>('/health').then(setHealth).catch(() => null);
    apiFetch<SystemStatus>('/system/status').then(setSystemStatus).catch(() => null);

    const interval = setInterval(() => {
      apiFetch<HealthStatus>('/health').then(setHealth).catch(() => null);
    }, 12000);

    // Load saved voice preference
    const saved = localStorage.getItem('jarvis-voice') as 'jarvis' | 'friday' | null;
    if (saved && (saved === 'jarvis' || saved === 'friday')) setVoice(saved);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    localStorage.setItem('jarvis-voice', voice);
  }, [voice]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#05080f] text-iron-100 relative">
      {/* HUD grid background */}
      <div className="absolute inset-0 hud-grid opacity-40 pointer-events-none" />
      <div className="absolute inset-0 pointer-events-none" style={{
        background: 'radial-gradient(ellipse 70% 45% at 50% -5%, rgba(0,229,255,0.09), transparent), radial-gradient(ellipse 45% 35% at 92% 88%, rgba(201,162,39,0.06), transparent)'
      }} />

      <Sidebar
        open={sidebarOpen}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        voice={voice}
        onVoiceChange={setVoice}
      />

      <div className="flex flex-1 flex-col min-w-0 relative z-10">
        <Header
          status={health?.status || 'unknown'}
          version={health?.version || '1.0.0'}
          onMenuToggle={() => setSidebarOpen(!sidebarOpen)}
          voice={voice}
          onVoiceChange={setVoice}
        />

        <main className="flex-1 overflow-hidden relative">
          {activeTab === 'chat' && <ChatInterface voice={voice} onVoiceChange={setVoice} />}
          {activeTab === 'status' && <StatusPanel systemStatus={systemStatus} health={health} />}
          {activeTab === 'voice' && <VoiceControl voice={voice} onVoiceChange={setVoice} />}
        </main>
      </div>
    </div>
  );
}

export default App;
