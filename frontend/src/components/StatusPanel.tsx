import { useEffect, useState } from 'react';
import { Server, Brain, Mic, Lock, Activity, Database } from 'lucide-react';
import { apiFetch } from '../hooks/useApi';
import type { SystemStatus, HealthStatus, AIHealth, VoiceStatus, PermissionStatus } from '../types';

export function StatusPanel({ systemStatus, health }: { systemStatus: SystemStatus | null; health: HealthStatus | null }) {
  const [aiHealth, setAiHealth] = useState<AIHealth | null>(null);
  const [voiceStatus, setVoiceStatus] = useState<VoiceStatus | null>(null);
  const [permissions, setPermissions] = useState<PermissionStatus[]>([]);

  useEffect(() => {
    apiFetch<AIHealth>('/ai/health').then(setAiHealth).catch(() => null);
    apiFetch<VoiceStatus>('/voice/status').then(setVoiceStatus).catch(() => null);
    apiFetch<PermissionStatus[]>('/system/permissions').then(setPermissions).catch(() => null);
  }, []);

  const cards = [
    {
      title: 'System',
      icon: Server,
      data: [
        { label: 'App', value: systemStatus?.app_name || '—' },
        { label: 'Version', value: systemStatus?.version || '—' },
        { label: 'Environment', value: systemStatus?.environment || '—' },
        { label: 'Offline', value: systemStatus?.offline ? 'Yes' : 'No' },
      ],
    },
    {
      title: 'Health',
      icon: Activity,
      data: [
        { label: 'Status', value: health?.status || '—' },
        { label: 'Version', value: health?.version || '—' },
        { label: 'Environment', value: health?.environment || '—' },
      ],
    },
    {
      title: 'AI Engine',
      icon: Brain,
      data: [
        { label: 'Ollama', value: aiHealth?.ollama_connected ? 'Connected' : 'Fallback' },
        { label: 'Model', value: aiHealth?.default_model || '—' },
        { label: 'Mode', value: aiHealth?.mode || '—' },
        { label: 'Conversations', value: aiHealth?.conversations_active?.toString() || '0' },
        { label: 'Memory', value: aiHealth?.memory_enabled ? 'Enabled' : 'Disabled' },
      ],
    },
    {
      title: 'Voice',
      icon: Mic,
      data: [
        { label: 'Status', value: voiceStatus?.status || '—' },
        { label: 'Mode', value: voiceStatus?.mode || '—' },
        { label: 'STT', value: voiceStatus?.stt || '—' },
        { label: 'TTS', value: voiceStatus?.tts || '—' },
      ],
    },
  ];

  return (
    <div className="h-full overflow-y-auto p-4 sm:p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-iron-100">System Status</h2>
          <p className="text-sm text-iron-400 mt-1">Real-time overview of all JARVIS subsystems.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {cards.map((card) => {
            const Icon = card.icon;
            return (
              <div
                key={card.title}
                className="bg-iron-900 border border-iron-800 rounded-xl p-4 hover:border-iron-700 transition-colors"
              >
                <div className="flex items-center gap-2 mb-3">
                  <Icon className="w-4 h-4 text-jarvis-400" />
                  <h3 className="text-sm font-medium text-iron-200">{card.title}</h3>
                </div>
                <div className="space-y-2">
                  {card.data.map((item) => (
                    <div key={item.label} className="flex justify-between text-xs">
                      <span className="text-iron-500">{item.label}</span>
                      <span className="text-iron-300 font-mono">{item.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-iron-900 border border-iron-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-4">
              <Lock className="w-4 h-4 text-jarvis-400" />
              <h3 className="text-sm font-medium text-iron-200">Permissions</h3>
            </div>
            <div className="space-y-1.5 max-h-64 overflow-y-auto">
              {permissions.length === 0 && (
                <p className="text-xs text-iron-500">Loading permissions...</p>
              )}
              {permissions.map((perm) => (
                <div
                  key={perm.permission}
                  className="flex items-center justify-between text-xs px-2 py-1.5 rounded-md bg-iron-800/50"
                >
                  <span className="text-iron-300 font-mono">{perm.permission}</span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                      perm.granted
                        ? 'bg-emerald-500/10 text-emerald-400'
                        : 'bg-iron-700 text-iron-500'
                    }`}
                  >
                    {perm.granted ? 'GRANTED' : 'DENIED'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-iron-900 border border-iron-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-4">
              <Database className="w-4 h-4 text-jarvis-400" />
              <h3 className="text-sm font-medium text-iron-200">Active Grants</h3>
            </div>
            <div className="text-xs text-iron-400 space-y-1">
              {systemStatus?.permissions_granted && systemStatus.permissions_granted.length > 0 ? (
                systemStatus.permissions_granted.map((p) => (
                  <div key={p} className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    <span className="font-mono text-iron-300">{p}</span>
                  </div>
                ))
              ) : (
                <p>No active permission grants.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
