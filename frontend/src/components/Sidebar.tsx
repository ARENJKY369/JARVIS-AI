import { MessageSquare, BarChart3, Mic, Cpu, X, Play, Globe, Sparkles, ShieldCheck } from 'lucide-react';

interface SidebarProps {
  open: boolean;
  activeTab: 'chat' | 'status' | 'voice';
  onTabChange: (tab: 'chat' | 'status' | 'voice') => void;
  onToggle: () => void;
  voice: 'jarvis' | 'friday';
  onVoiceChange: (v: 'jarvis' | 'friday') => void;
}

const tabs = [
  { id: 'chat' as const, label: 'Command', icon: MessageSquare, desc: 'Chat • Skills • Media' },
  { id: 'voice' as const, label: 'Voice Studio', icon: Mic, desc: 'JARVIS / FRIDAY • Human' },
  { id: 'status' as const, label: 'Systems', icon: BarChart3, desc: 'Diagnostics • Permissions' },
];

export function Sidebar({ open, activeTab, onTabChange, onToggle, voice, onVoiceChange }: SidebarProps) {
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-[300px] border-r backdrop-blur-xl transform transition-all duration-300 ease-out flex flex-col ${
          open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-[84px] xl:w-[300px]'
        } bg-[#0a1220]/90 ${voice === 'friday' ? 'border-amber-500/10' : 'border-cyan-500/10'}`}
      >
        {/* Brand header */}
        <div className="flex items-center justify-between p-5 border-b border-white/[0.06] relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/[0.04] to-transparent pointer-events-none" />
          <div className="flex items-center gap-3 relative">
            <div className="relative w-10 h-10 rounded-full grid place-items-center border bg-[#0d1a2d]" style={{ borderColor: voice === 'friday' ? 'rgba(245,158,11,0.25)' : 'rgba(6,182,212,0.25)' }}>
              <Cpu className={`w-5 h-5 ${voice === 'friday' ? 'text-amber-300' : 'text-cyan-300'}`} />
              <div className="absolute inset-[-4px] rounded-full border border-dashed opacity-40 animate-spin" style={{ animationDuration: '12s', borderColor: voice === 'friday' ? '#f59e0b' : '#06b6d4' }} />
            </div>
            <div className="lg:hidden xl:block">
              <div className="font-bold tracking-[0.18em] text-[13px]">JARVIS OS</div>
              <div className="text-[10px] tracking-[0.2em] text-iron-500 uppercase">Iron Man • HUD • v2</div>
            </div>
          </div>
          <button onClick={onToggle} className="lg:hidden p-2 rounded-xl hover:bg-white/5 border border-white/5">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1.5 flex-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`w-full group flex items-center gap-3 px-3.5 py-3 rounded-xl text-left transition-all relative overflow-hidden ${
                  isActive
                    ? voice === 'friday'
                      ? 'bg-amber-500/10 text-amber-200 border border-amber-500/20 shadow-[0_0_16px_rgba(245,158,11,0.12)]'
                      : 'bg-cyan-500/10 text-cyan-100 border border-cyan-500/20 shadow-[0_0_16px_rgba(6,182,212,0.15)]'
                    : 'text-iron-400 hover:text-iron-200 hover:bg-white/[0.04] border border-transparent'
                }`}
              >
                {isActive && <div className={`absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 rounded-full ${voice === 'friday' ? 'bg-amber-400' : 'bg-cyan-400'}`} />}
                <div className={`w-9 h-9 rounded-lg grid place-items-center shrink-0 transition-all ${isActive ? (voice === 'friday' ? 'bg-amber-500/15' : 'bg-cyan-500/15') : 'bg-white/[0.04] group-hover:bg-white/[0.07]'}`}>
                  <Icon className="w-[18px] h-[18px]" />
                </div>
                <div className="lg:hidden xl:block min-w-0">
                  <div className="text-[13px] font-semibold tracking-wide leading-none">{tab.label}</div>
                  <div className="text-[10px] text-iron-500 mt-1 tracking-wide leading-none">{tab.desc}</div>
                </div>
              </button>
            );
          })}

          <div className="pt-6 space-y-3">
            <div className="px-3 text-[10px] tracking-[0.18em] text-iron-500 uppercase lg:hidden xl:block">Quick Actions</div>
            <div className="grid gap-1.5">
              {[
                { icon: Play, label: 'Play video / YouTube', q: 'play lo-fi hip hop' },
                { icon: Globe, label: 'Open website', q: 'open github.com' },
                { icon: Sparkles, label: 'Ask ChatGPT', q: 'ask chatgpt about AI' },
              ].map((a) => (
                <button
                  key={a.label}
                  onClick={() => onTabChange('chat')}
                  className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-xs text-iron-400 hover:text-iron-200 hover:bg-white/[0.04] border border-white/[0.03] hover:border-white/[0.06] transition-all lg:hidden xl:flex"
                >
                  <a.icon className="w-3.5 h-3.5" />
                  <span className="truncate">{a.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Voice toggle in sidebar for mobile */}
          <div className="sm:hidden pt-4">
            <div className="px-3 text-[10px] tracking-[0.18em] text-iron-500 uppercase mb-2">Voice — Human-like</div>
            <div className="flex gap-1 p-1 rounded-full bg-black/30 border border-white/10">
              <button
                onClick={() => onVoiceChange('jarvis')}
                className={`flex-1 py-2 rounded-full text-xs font-semibold ${voice === 'jarvis' ? 'bg-cyan-500/20 text-cyan-200 border border-cyan-400/20' : 'text-iron-500'}`}
              >
                JARVIS
              </button>
              <button
                onClick={() => onVoiceChange('friday')}
                className={`flex-1 py-2 rounded-full text-xs font-semibold ${voice === 'friday' ? 'bg-amber-500/20 text-amber-200 border border-amber-400/20' : 'text-iron-500'}`}
              >
                FRIDAY
              </button>
            </div>
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-white/[0.06] space-y-3">
          <div className={`rounded-xl p-3 border ${voice === 'friday' ? 'bg-amber-500/[0.06] border-amber-500/10' : 'bg-cyan-500/[0.06] border-cyan-500/10'}`}>
            <div className="flex items-center gap-2 text-[11px] font-semibold tracking-wide">
              <ShieldCheck className={`w-3.5 h-3.5 ${voice === 'friday' ? 'text-amber-400' : 'text-cyan-400'}`} />
              <span className={voice === 'friday' ? 'text-amber-200' : 'text-cyan-200'}>Offline • Secure • Private</span>
            </div>
            <div className="text-[10px] text-iron-500 mt-1 leading-relaxed">
              Local LLM • Formant v2 Humanized TTS • No cloud. Voice crackle fixed.
            </div>
          </div>
          <div className="text-[10px] text-iron-600 tracking-widest uppercase lg:hidden xl:block text-center">At your service, sir • HUD v2</div>
        </div>
      </aside>
    </>
  );
}
