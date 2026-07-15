import { Menu, Activity, Zap, Cpu, Volume2 } from 'lucide-react';

interface HeaderProps {
  status: string;
  version: string;
  onMenuToggle: () => void;
  voice: 'jarvis' | 'friday';
  onVoiceChange: (v: 'jarvis' | 'friday') => void;
}

export function Header({ status, version, onMenuToggle, voice, onVoiceChange }: HeaderProps) {
  const isOnline = status === 'healthy' || status === 'ok' || status === 'operational';

  return (
    <header className="flex items-center justify-between px-4 sm:px-6 py-3 border-b border-cyan-500/10 bg-[#0a1220]/80 backdrop-blur-xl relative overflow-hidden">
      {/* subtle top glow line */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-400/40 to-transparent" />

      <div className="flex items-center gap-4">
        <button
          onClick={onMenuToggle}
          className="p-2 rounded-xl hover:bg-white/[0.06] border border-transparent hover:border-white/10 transition-all lg:hidden"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3">
          <div className="relative w-9 h-9 rounded-full reactor-ring grid place-items-center bg-[#0d1a2d]">
            <div className="w-5 h-5 rounded-full reactor-core animate-pulse" />
            <div className={`absolute inset-[-3px] rounded-full border ${voice === 'friday' ? 'border-amber-400/30' : 'border-cyan-400/30'} animate-spin`} style={{ animationDuration: '8s' }} />
          </div>
          <div>
            <h1 className="text-[15px] font-bold tracking-[0.18em] flex items-center gap-2">
              <span className={voice === 'friday' ? 'text-amber-200' : 'text-cyan-300 jarvis-text-glow'}>JARVIS</span>
              <span className="text-[10px] font-normal tracking-[0.2em] text-iron-500 border border-white/10 rounded-full px-2 py-0.5">OS</span>
            </h1>
            <div className="flex items-center gap-2 text-[10px] tracking-widest text-iron-500">
              <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-emerald-400 shadow-[0_0_6px_#10b981]' : 'bg-red-400'}`} />
              <span className="uppercase">{isOnline ? 'Online • Primary Systems Nominal' : status}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Voice toggle - only two options as requested */}
        <div className="hidden sm:flex items-center gap-1 p-1 rounded-full bg-black/30 border border-white/10 backdrop-blur">
          <button
            onClick={() => onVoiceChange('jarvis')}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold tracking-wide transition-all flex items-center gap-1.5 ${
              voice === 'jarvis' ? 'bg-cyan-500/20 text-cyan-200 border border-cyan-400/30 shadow-[0_0_10px_rgba(6,182,212,0.2)]' : 'text-iron-500 hover:text-iron-300'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" /> JARVIS
          </button>
          <button
            onClick={() => onVoiceChange('friday')}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold tracking-wide transition-all flex items-center gap-1.5 ${
              voice === 'friday' ? 'bg-amber-500/20 text-amber-200 border border-amber-400/30 shadow-[0_0_10px_rgba(245,158,11,0.2)]' : 'text-iron-500 hover:text-iron-300'
            }`}
          >
            <Zap className="w-3.5 h-3.5" /> FRIDAY
          </button>
        </div>

        <div className="hidden md:flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5 text-iron-400">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-mono">{version}</span>
          </div>
          <div className="flex items-center gap-1.5 text-iron-500">
            <Volume2 className="w-3.5 h-3.5" />
            <span className="uppercase tracking-widest text-[10px]">{voice === 'jarvis' ? 'Deep • 92Hz • Human' : 'Cool • 182Hz • Human'}</span>
          </div>
        </div>

        <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]' : 'bg-red-500'}`} />
      </div>
    </header>
  );
}
