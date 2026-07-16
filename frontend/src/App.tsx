import { useState, useEffect, useRef } from 'react';
import {
  Settings, Bell, Mic, Wifi, Power, Search, FolderOpen, Play, Terminal,
  MessageSquare, User, Cog, Wrench, ShieldCheck, Cloud,
  Zap, Activity
} from 'lucide-react';

export default function App() {
  const [listening, setListening] = useState(false);
  const [micPulse, setMicPulse] = useState(false);
  const [coreSpin, setCoreSpin] = useState(0);
  const [waveBars, setWaveBars] = useState<number[]>([]);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Animate core rotation
  useEffect(() => {
    const id = setInterval(() => setCoreSpin(s => s + 0.5), 16);
    return () => clearInterval(id);
  }, []);

  // Animate waveform bars
  useEffect(() => {
    const id = setInterval(() => {
      const count = 24;
      const bars = Array.from({ length: count }, () => Math.random() * 100);
      setWaveBars(bars);
    }, 120);
    return () => clearInterval(id);
  }, []);

  // Canvas particle float
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    let w = canvas.width = window.innerWidth;
    let h = canvas.height = window.innerHeight;
    window.addEventListener('resize', () => { w = canvas.width = window.innerWidth; h = canvas.height = window.innerHeight; });
    const particles: { x: number; y: number; r: number; dx: number; dy: number; alpha: number }[] = [];
    for (let i = 0; i < 80; i++) {
      particles.push({
        x: Math.random() * w,
        y: Math.random() * h,
        r: Math.random() * 1.5 + 0.5,
        dx: (Math.random() - 0.5) * 0.4,
        dy: (Math.random() - 0.5) * 0.4,
        alpha: Math.random() * 0.5 + 0.2,
      });
    }
    let anim = 0;
    const loop = () => {
      anim++;
      ctx.clearRect(0, 0, w, h);
      for (const p of particles) {
        p.x += p.dx; p.y += p.dy;
        if (p.x < 0 || p.x > w) p.dx *= -1;
        if (p.y < 0 || p.y > h) p.dy *= -1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 229, 255, ${p.alpha})`;
        ctx.fill();
      }
      requestAnimationFrame(loop);
    };
    loop();
  }, []);

  const toggleMic = () => {
    setListening(!listening);
    setMicPulse(true);
    setTimeout(() => setMicPulse(false), 600);
  };

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-[#03070a] text-[#d6e6f2] font-sans selection:bg-cyan-400/30">
      {/* Background texture */}
      <div className="pointer-events-none fixed inset-0 z-0 opacity-[0.07]"
        style={{
          backgroundImage:
            'linear-gradient(rgba(0,229,255,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(0,229,255,0.4) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
          maskImage: 'radial-gradient(ellipse at center, black 40%, transparent 80%)',
        }}
      />
      {/* Floating particles canvas */}
      <canvas ref={canvasRef} className="pointer-events-none fixed inset-0 z-0" />

      {/* Top Navigation */}
      <nav className="relative z-50 flex items-center justify-between px-6 py-4 border-b border-cyan-500/10 backdrop-blur-xl bg-[#03070a]/60">
        <div className="flex items-center gap-8">
          <a href="#" className="text-xs uppercase tracking-[0.2em] text-cyan-300 hover:text-white transition-colors">System</a>
          <a href="#" className="text-xs uppercase tracking-[0.2em] text-cyan-300 hover:text-white transition-colors">Network</a>
          <a href="#" className="text-xs uppercase tracking-[0.2em] text-cyan-300 hover:text-white transition-colors">Audio</a>
          <a href="#" className="text-xs uppercase tracking-[0.2em] text-cyan-300 hover:text-white transition-colors">Display</a>
          <a href="#" className="text-xs uppercase tracking-[0.2em] text-cyan-300 hover:text-white transition-colors">Controls</a>
          <a href="#" className="text-xs uppercase tracking-[0.2em] text-cyan-300 hover:text-white transition-colors">Devices</a>
        </div>
        <div className="flex items-center gap-4">
          {[
            { icon: Settings, label: 'Settings' },
            { icon: Bell, label: 'Notifications' },
            { icon: Mic, label: 'Voice' },
            { icon: Wifi, label: 'Connectivity' },
            { icon: Power, label: 'Power' },
          ].map(({ icon: Icon, label }) => (
            <button key={label} title={label} className="relative p-2 rounded-full hover:bg-cyan-400/10 transition-colors group">
              <Icon className="w-5 h-5 text-cyan-300 group-hover:text-white transition-colors" />
              <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-[10px] text-cyan-200 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">{label}</span>
            </button>
          ))}
        </div>
      </nav>

      <main className="relative z-10 grid grid-cols-[320px_1fr_320px] gap-6 px-6 pt-6 pb-28">
        {/* LEFT PANEL — Operational Intelligence */}
        <aside className="space-y-6">
          {/* System Health */}
          <section className="rounded-2xl border border-cyan-500/15 bg-gradient-to-br from-[#0a1220]/80 to-[#03070a]/80 backdrop-blur-2xl p-5 shadow-2xl shadow-cyan-900/10">
            <h3 className="text-[10px] uppercase tracking-[0.2em] text-cyan-400 mb-4">System Health</h3>
            <div className="grid grid-cols-2 gap-4">
              <Gauge label="CPU" value={42} color="#00e5ff" />
              <Gauge label="GPU" value={68} color="#0099ff" />
              <Gauge label="RAM" value={78} color="#00e5ff" />
              <Gauge label="Storage" value={34} color="#0099ff" />
            </div>
            <div className="mt-4 flex items-center gap-3">
              <div className="w-8 h-8 rounded-full border-2 border-cyan-400/30 flex items-center justify-center text-[10px] font-bold text-cyan-300">92%</div>
              <div>
                <div className="text-xs text-cyan-200">Battery Health</div>
                <div className="text-[10px] text-cyan-500">Excellent condition</div>
              </div>
            </div>
          </section>

          {/* Environment */}
          <section className="rounded-2xl border border-cyan-500/15 bg-gradient-to-br from-[#0a1220]/80 to-[#03070a]/80 backdrop-blur-2xl p-5 shadow-2xl shadow-cyan-900/10">
            <h3 className="text-[10px] uppercase tracking-[0.2em] text-cyan-400 mb-3">Environment</h3>
            <div className="flex items-center gap-3 mb-3">
              <Cloud className="w-6 h-6 text-cyan-300" />
              <div>
                <div className="text-sm font-medium">18°C · Clear</div>
                <div className="text-[10px] text-cyan-500">Bucharest, RO</div>
              </div>
            </div>
            <LiveGraph />
          </section>

          {/* Notifications */}
          <section className="rounded-2xl border border-cyan-500/15 bg-gradient-to-br from-[#0a1220]/80 to-[#03070a]/80 backdrop-blur-2xl p-5 shadow-2xl shadow-cyan-900/10">
            <h3 className="text-[10px] uppercase tracking-[0.2em] text-cyan-400 mb-3">Notifications</h3>
            <ul className="space-y-3 text-xs">
              <li className="flex items-start gap-2"><span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1 shrink-0" /><span>AI agent completed analysis</span></li>
              <li className="flex items-start gap-2"><span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1 shrink-0" /><span>Storage usage at 34%</span></li>
              <li className="flex items-start gap-2"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1 shrink-0" /><span>Network stable · 942 Mbps</span></li>
            </ul>
          </section>
        </aside>

        {/* CENTER STAGE — AI Core + Conversation */}
        <section className="flex flex-col items-center justify-start pt-4">
          {/* Holographic AI Core */}
          <div className="relative w-[360px] h-[360px] flex items-center justify-center">
            {/* Rotating outer ring */}
            <div className="absolute w-[340px] h-[340px] rounded-full border border-cyan-500/20 animate-[spin_20s_linear_infinite]"
                 style={{ transform: `rotate(${coreSpin}deg)` }}>
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_12px_#00e5ff]" />
            </div>
            {/* Middle ring */}
            <div className="absolute w-[280px] h-[280px] rounded-full border border-cyan-400/25 animate-[spin_12s_linear_infinite_reverse]"
                 style={{ transform: `rotate(${-coreSpin * 1.5}deg)` }}>
              <div className="absolute top-1/2 right-0 translate-x-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-blue-400 shadow-[0_0_12px_#0099ff]" />
            </div>
            {/* Inner ring */}
            <div className="absolute w-[220px] h-[220px] rounded-full border-2 border-cyan-300/40 animate-[spin_8s_linear_infinite]"
                 style={{ transform: `rotate(${coreSpin * 0.8}deg)` }} />

            {/* Radar sweep */}
            <div className="absolute w-[260px] h-[260px] rounded-full overflow-hidden" style={{ transform: `rotate(${coreSpin * 3}deg)` }}>
              <div className="absolute top-1/2 left-1/2 w-[130px] h-[260px] origin-top-left bg-gradient-to-r from-cyan-400/40 via-cyan-400/10 to-transparent blur-md animate-[spin_4s_linear_infinite]" />
            </div>

            {/* Neural dots */}
            <div className="absolute w-[200px] h-[200px] rounded-full border border-cyan-500/10">
              {Array.from({ length: 12 }).map((_, i) => (
                <div key={i} className="absolute w-1 h-1 rounded-full bg-cyan-300 animate-[pulse_2s_ease-in-out_infinite]"
                     style={{
                       top: `${20 + 60 * Math.sin(i * 0.52)}%`,
                       left: `${20 + 60 * Math.cos(i * 0.52)}%`,
                       animationDelay: `${i * 0.2}s`,
                       boxShadow: '0 0 6px #00e5ff',
                     }} />
              ))}
            </div>

            {/* Core center */}
            <div className="relative z-20 w-20 h-20 rounded-full bg-gradient-to-tr from-cyan-400 via-blue-500 to-cyan-300 shadow-[0_0_60px_rgba(0,229,255,0.6),inset_0_0_20px_rgba(255,255,255,0.2)] animate-[pulse_3s_ease-in-out_infinite] ring-4 ring-cyan-400/20 flex items-center justify-center">
              <Zap className="w-8 h-8 text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]" />
            </div>
          </div>

          {/* Conversation */}
          <div className="w-full max-w-lg mt-8 rounded-2xl border border-cyan-500/15 bg-gradient-to-b from-[#0a1220]/70 to-[#03070a]/80 backdrop-blur-2xl p-6 shadow-2xl shadow-cyan-900/10">
            <h2 className="text-xs uppercase tracking-[0.25em] text-cyan-400 mb-4">Conversational AI</h2>
            <div className="space-y-4">
              <div className="flex gap-3 items-start">
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-400 to-blue-500 flex items-center justify-center text-xs font-bold">AI</div>
                <div className="bg-[#0a1220]/60 border border-cyan-500/10 rounded-xl px-4 py-3 text-sm text-cyan-50 shadow-inner">
                  Good evening, sir. All primary systems nominal. How may I assist you?
                </div>
              </div>
              <div className="flex gap-3 items-start">
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-amber-400 to-amber-600 flex items-center justify-center text-xs font-bold">ME</div>
                <div className="bg-[#081024]/60 border border-cyan-500/10 rounded-xl px-4 py-3 text-sm text-cyan-50 shadow-inner">
                  Launch file manager and show system diagnostics.
                </div>
              </div>
            </div>

            {/* Waveform visualization */}
            <div className="mt-5 h-12 flex items-end gap-[3px]">
              {waveBars.map((h, i) => (
                <div key={i} className="flex-1 rounded-full bg-gradient-to-t from-cyan-700/60 to-cyan-300/90 transition-all duration-100"
                  style={{ height: `${Math.max(10, h)}%`, opacity: 0.6 + (h / 200) }} />
              ))}
            </div>

            {/* Mic + Input */}
            <div className="mt-5 flex items-center gap-3">
              <button onClick={toggleMic}
                className={`relative w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg ${listening ? 'bg-rose-500/20 ring-4 ring-rose-400/30 shadow-rose-500/40' : 'bg-cyan-500/10 ring-4 ring-cyan-400/20 shadow-cyan-500/20'}`}>
                <Mic className={`w-6 h-6 transition-transform duration-300 ${listening ? 'text-rose-400 scale-110' : 'text-cyan-300'}`} />
                {micPulse && <span className="absolute inset-0 rounded-full border-2 border-cyan-400 animate-[ping_1s_ease-out_infinite]" />}
              </button>
              <div className="flex-1 relative">
                <input type="text" placeholder="Speak or type a command..."
                  className="w-full rounded-xl border border-cyan-500/20 bg-[#03070a]/60 px-4 py-3 text-sm text-cyan-50 placeholder-cyan-700 focus:outline-none focus:border-cyan-400 focus:shadow-[0_0_0_3px_rgba(0,229,255,0.15)] transition-all backdrop-blur-md" />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-cyan-600">Press ENTER</span>
              </div>
            </div>
          </div>
        </section>

        {/* RIGHT PANEL — Contextual Info */}
        <aside className="space-y-6">
          {/* 3D Holographic Globe */}
          <section className="rounded-2xl border border-cyan-500/15 bg-gradient-to-br from-[#0a1220]/80 to-[#03070a]/80 backdrop-blur-2xl p-5 shadow-2xl shadow-cyan-900/10">
            <h3 className="text-[10px] uppercase tracking-[0.2em] text-cyan-400 mb-4">Global Position</h3>
            <div className="relative w-full h-48 flex items-center justify-center">
              <div className="w-32 h-32 rounded-full bg-gradient-to-br from-cyan-900/40 to-blue-900/20 border border-cyan-400/20 shadow-[0_0_40px_rgba(0,229,255,0.25)] relative overflow-hidden animate-[spin_30s_linear_infinite]">
                <div className="absolute inset-0 rounded-full bg-[radial-gradient(circle_at_30%_30%,rgba(0,229,255,0.15),transparent_70%)]" />
                {/* Grid lines */}
                <div className="absolute top-1/2 left-0 right-0 h-px bg-cyan-400/20" />
                <div className="absolute left-1/2 top-0 bottom-0 w-px bg-cyan-400/20" />
                <div className="absolute top-[30%] left-0 right-0 h-px bg-cyan-400/10" />
                <div className="absolute left-[30%] top-0 bottom-0 w-px bg-cyan-400/10" />
                {/* Dot */}
                <div className="absolute top-[40%] left-[55%] w-2 h-2 rounded-full bg-cyan-300 shadow-[0_0_8px_#00e5ff] animate-[pulse_2s_ease-in-out_infinite]" />
              </div>
            </div>
            <div className="mt-3 text-xs text-cyan-200">Bucharest, Romania (44.4268° N, 26.1025° E)</div>
          </section>

          {/* Weather + AI Processes */}
          <section className="rounded-2xl border border-cyan-500/15 bg-gradient-to-br from-[#0a1220]/80 to-[#03070a]/80 backdrop-blur-2xl p-5 shadow-2xl shadow-cyan-900/10">
            <h3 className="text-[10px] uppercase tracking-[0.2em] text-cyan-400 mb-3">Weather & Forecast</h3>
            <div className="flex items-center gap-3 mb-4">
              <SunIcon />
              <div>
                <div className="text-lg font-medium">18°C</div>
                <div className="text-[10px] text-cyan-500">Clear skies · 12 km/h wind</div>
              </div>
            </div>
            <div className="h-16 flex items-end gap-1">
              {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map((d,i) => (
                <div key={d} className="flex-1 flex flex-col items-center gap-1">
                  <div className="w-full rounded-t bg-gradient-to-t from-cyan-700/40 to-cyan-400/80" style={{ height: `${20 + Math.random()*60}%` }} />
                  <span className="text-[9px] text-cyan-600">{d}</span>
                </div>
              ))}
            </div>
          </section>

          {/* Active AI Processes */}
          <section className="rounded-2xl border border-cyan-500/15 bg-gradient-to-br from-[#0a1220]/80 to-[#03070a]/80 backdrop-blur-2xl p-5 shadow-2xl shadow-cyan-900/10">
            <h3 className="text-[10px] uppercase tracking-[0.2em] text-cyan-400 mb-3">Active AI Processes</h3>
            <ul className="space-y-2 text-xs">
              <Process label="Neural Analysis" pct={92} />
              <Process label="Voice Synthesis" pct={67} />
              <Process label="Memory Indexing" pct={45} />
              <Process label="Security Monitor" pct={88} />
            </ul>
          </section>

          {/* Storage Analytics */}
          <section className="rounded-2xl border border-cyan-500/15 bg-gradient-to-br from-[#0a1220]/80 to-[#03070a]/80 backdrop-blur-2xl p-5 shadow-2xl shadow-cyan-900/10">
            <h3 className="text-[10px] uppercase tracking-[0.2em] text-cyan-400 mb-3">Storage Analytics</h3>
            <div className="flex items-end gap-4 h-16">
              <div className="w-8 h-16 rounded-full bg-gradient-to-t from-cyan-900/30 to-cyan-400/70 shadow-[0_0_10px_#00e5ff] animate-[pulse_4s_ease-in-out_infinite]" />
              <div className="w-8 h-12 rounded-full bg-gradient-to-t from-cyan-900/30 to-cyan-400/70 shadow-[0_0_10px_#00e5ff]" />
              <div className="w-8 h-16 rounded-full bg-gradient-to-t from-cyan-900/30 to-cyan-400/70 shadow-[0_0_10px_#00e5ff] animate-[pulse_3s_ease-in-out_infinite]" />
            </div>
            <div className="mt-2 flex justify-between text-[10px] text-cyan-600">
              <span>2.4 TB used</span>
              <span>780 GB free</span>
            </div>
          </section>

          {/* Security + Uptime */}
          <section className="rounded-2xl border border-cyan-500/15 bg-gradient-to-br from-[#0a1220]/80 to-[#03070a]/80 backdrop-blur-2xl p-5 shadow-2xl shadow-cyan-900/10">
            <h3 className="text-[10px] uppercase tracking-[0.2em] text-cyan-400 mb-3">System Uptime & Security</h3>
            <div className="flex items-center gap-3 mb-3">
              <ShieldCheck className="w-6 h-6 text-emerald-400" />
              <div className="text-sm">All systems protected</div>
            </div>
            <div className="text-xs text-cyan-500">Uptime: 14d 7h 32m · Last audit: 2 min ago</div>
          </section>
        </aside>
      </main>

      {/* Bottom Dock */}
      <nav className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 px-6 py-3 rounded-full border border-cyan-500/20 bg-[#03070a]/70 backdrop-blur-3xl shadow-[0_0_40px_rgba(0,229,255,0.15)]">
        {[
          { icon: Search, label: 'Search' },
          { icon: FolderOpen, label: 'Files' },
          { icon: Play, label: 'Media' },
          { icon: Terminal, label: 'Terminal' },
          { icon: MessageSquare, label: 'Messages' },
          { icon: User, label: 'Contacts' },
          { icon: Cog, label: 'Settings' },
          { icon: Wrench, label: 'Diagnostics' },
          { icon: Activity, label: 'AI Tools' },
        ].map(({ icon: Icon, label }) => (
          <a key={label} href="#" title={label}
            className="group relative p-3 rounded-xl hover:bg-cyan-400/10 transition-colors">
            <Icon className="w-5 h-5 text-cyan-300 group-hover:text-white drop-shadow-[0_0_4px_rgba(0,229,255,0.5)] transition-colors" />
            <span className="absolute -top-8 left-1/2 -translate-x-1/2 text-[10px] text-cyan-200 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap bg-[#0a1220] px-2 py-0.5 rounded-md border border-cyan-500/20 shadow-lg">{label}</span>
          </a>
        ))}
      </nav>
    </div>
  );
}

/* Sub-components */
function Gauge({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="relative w-16 h-16">
      <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="rgba(0,229,255,0.1)" strokeWidth="2.5" />
        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke={color} strokeWidth="2.5" strokeDasharray={`${value}, 100`} strokeLinecap="round" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-[9px] text-cyan-500">{label}</span>
      </div>
    </div>
  );
}

function LiveGraph() {
  return (
    <svg viewBox="0 0 200 60" className="w-full h-14 text-cyan-400" preserveAspectRatio="none">
      <defs>
        <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#00e5ff" stopOpacity="0.6" />
          <stop offset="100%" stopColor="#00e5ff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d="M0,40 Q20,20 40,35 T80,25 T120,30 T160,15 T200,20 L200,60 L0,60 Z" fill="url(#lineGrad)" />
      <path d="M0,40 Q20,20 40,35 T80,25 T120,30 T160,15 T200,20" fill="none" stroke="#00e5ff" strokeWidth="1.5" />
      <circle cx="160" cy="15" r="2" fill="#00e5ff" className="animate-[pulse_1s_ease-in-out_infinite]" />
    </svg>
  );
}

function Process({ label, pct }: { label: string; pct: number }) {
  return (
    <li>
      <div className="flex justify-between text-[10px] mb-1 text-cyan-300">
        <span>{label}</span>
        <span>{pct}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-[#03070a] overflow-hidden border border-cyan-500/10">
        <div className="h-full rounded-full bg-gradient-to-r from-cyan-700 to-cyan-300 shadow-[0_0_6px_#00e5ff] transition-all duration-500" style={{ width: `${pct}%` }} />
      </div>
    </li>
  );
}

function SunIcon() {
  return (
    <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-amber-300 to-amber-500 shadow-[0_0_20px_rgba(245,158,11,0.4)] flex items-center justify-center animate-[pulse_3s_ease-in-out_infinite]">
      <div className="w-5 h-5 rounded-full bg-white shadow-[0_0_10px_rgba(255,255,255,0.8)]" />
    </div>
  );
}
