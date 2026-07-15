export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  model?: string;
  durationMs?: number;
}

export interface SystemStatus {
  app_name: string;
  version: string;
  environment: string;
  offline: boolean;
  permissions_granted: string[];
}

export interface HealthStatus {
  status: string;
  version: string;
  environment: string;
  offline: boolean;
}

export interface AIHealth {
  ollama_connected: boolean;
  default_model: string;
  conversations_active: number;
  mode: string;
  memory_enabled: boolean;
}

export interface VoiceStatus {
  status: string;
  mode: string;
  stt: string;
  tts: string;
  note: string;
}

export interface MemoryEntry {
  id: string;
  content: string;
  timestamp: number;
  metadata: Record<string, unknown>;
}

export interface PermissionStatus {
  permission: string;
  granted: boolean;
}
