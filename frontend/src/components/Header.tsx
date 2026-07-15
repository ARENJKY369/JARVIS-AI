import { Menu, Activity, Shield } from 'lucide-react';

interface HeaderProps {
  status: string;
  version: string;
  onMenuToggle: () => void;
}

export function Header({ status, version, onMenuToggle }: HeaderProps) {
  const isOnline = status === 'healthy';

  return (
    <header className="flex items-center justify-between px-4 py-3 border-b border-iron-800 bg-iron-900/80 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="p-2 rounded-lg hover:bg-iron-800 transition-colors lg:hidden"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          <div className={`w-2.5 h-2.5 rounded-full ${isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
          <h1 className="text-lg font-semibold tracking-tight">
            JARVIS <span className="text-jarvis-400 font-light">OS</span>
          </h1>
        </div>
      </div>

      <div className="flex items-center gap-4 text-sm text-iron-400">
        <div className="hidden sm:flex items-center gap-1.5">
          <Activity className="w-4 h-4" />
          <span className="capitalize">{status}</span>
        </div>
        <div className="hidden sm:flex items-center gap-1.5">
          <Shield className="w-4 h-4" />
          <span>v{version}</span>
        </div>
      </div>
    </header>
  );
}
