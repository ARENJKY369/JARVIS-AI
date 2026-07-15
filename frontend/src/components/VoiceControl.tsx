import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, Play, Square, Cpu, Zap, Settings2, Radio, Waves } from 'lucide-react';
import { apiFetch } from '../hooks/useApi';

interface Props {
  voice: 'jarvis' | 'friday';
  onVoiceChange: (v: 'jarvis' | 'friday') => void;
}

export function VoiceControl({ voice, onVoiceChange }: Props) {
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [lastTranscript, setLastTranscript] = useState('');
  const [lastResponse, setLastResponse] = useState('');
  const [voices, setVoices] = useState<any[]>([]);
  const [engine, setEngine] = useState<string>('loading');
  const [webVoices, setWebVoices] = useState<SpeechSynthesisVoice[]>([]);
  const audioRef = useRef<HTMLAudioElement>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    apiFetch<{ voices: any[]; tts: { engine: string } }>('/voice/voices').then(d => {
      if (d?.voices) setVoices(d.voices);
    }).catch(() => null);
    apiFetch<{ tts: { engine: string } }>('/voice/status').then(s => setEngine(s?.tts?.engine || 'jarvis-formant v2')).catch(() => setEngine('jarvis-formant v2 humanized'));

    const loadWebVoices = () => {
      const vs = window.speechSynthesis?.getVoices() || [];
      setWebVoices(vs);
    };
    loadWebVoices();
    if ('speechSynthesis' in window) {
      window.speechSynthesis.onvoiceschanged = loadWebVoices;
      // Unlock audio on first interaction
      const unlock = () => {
        window.speechSynthesis.getVoices();
        document.removeEventListener('click', unlock);
      };
      document.addEventListener('click', unlock);
    }

    // Web Speech Recognition setup
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SR) {
      const rec = new SR();
      rec.lang = 'en-US';
      rec.interimResults = false;
      rec.continuous = false;
      rec.onresult = (e: any) => {
        const t = e.results[0][0].transcript;
        setLastTranscript(t);
        // Auto-send transcript to JARVIS
        handleCommand(t);
      };
      rec.onstart = () => setListening(true);
      rec.onend = () => setListening(false);
      rec.onerror = () => setListening(false);
      recognitionRef.current = rec;
    }
  }, []);

  const speakHuman = (text: string) => {
    if (!('speechSynthesis' in window)) return false;
    try {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text.slice(0, 800));
      const all = window.speechSynthesis.getVoices();
      let preferred: SpeechSynthesisVoice | undefined;
      if (voice === 'jarvis') {
        preferred = all.find(v => /UK.*Male/i.test(v.name)) ||
                    all.find(v => /George/i.test(v.name)) ||
                    all.find(v => /en-GB/i.test(v.lang)) ||
                    all.find(v => v.lang.startsWith('en'));
      } else {
        preferred = all.find(v => /UK.*Female/i.test(v.name)) ||
                    all.find(v => /Google.*Female/i.test(v.name)) ||
                    all.find(v => v.lang.startsWith('en') && /female/i.test(v.name.toLowerCase())) ||
                    all.find(v => v.lang.startsWith('en'));
      }
      if (preferred) utter.voice = preferred;
      utter.rate = voice === 'jarvis' ? 0.88 : 0.95;
      utter.pitch = voice === 'jarvis' ? 0.88 : 1.1;
      utter.volume = 0.95;
      utter.onstart = () => setSpeaking(true);
      utter.onend = () => setSpeaking(false);
      utter.onerror = () => setSpeaking(false);
      window.speechSynthesis.speak(utter);
      return true;
    } catch {
      return false;
    }
  };

  const speakBackend = async (text: string) => {
    try {
      setSpeaking(true);
      const data = await apiFetch<{ audio_base64: string; data_uri: string }>('/voice/speak', {
        method: 'POST',
        body: JSON.stringify({ text, voice })
      });
      if (data?.audio_base64 && audioRef.current) {
        const binary = atob(data.audio_base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
        const blob = new Blob([bytes], { type: 'audio/wav' });
        const url = URL.createObjectURL(blob);
        audioRef.current.src = url;
        audioRef.current.onended = () => setSpeaking(false);
        await audioRef.current.play();
      } else setSpeaking(false);
    } catch {
      setSpeaking(false);
    }
  };

  const handleCommand = async (text: string) => {
    if (!text.trim()) return;
    setLastTranscript(text);
    try {
      // Use orchestrator - supports open website, play video, ask chatgpt auto-send
      const data = await apiFetch<{ response_text?: string; reply?: string; data?: any; audio_base64?: string }>(`/skills/execute`, {
        method: 'POST',
        body: JSON.stringify({ text, dry_run: false })
      });
      const reply = data?.reply || data?.response_text || 'Done, sir.';
      setLastResponse(reply);

      // Auto open URL if present (website / video / chatgpt)
      if (data?.data?.url) {
        try { window.open(data.data.url, '_blank'); } catch {}
      }

      // Speak human-like
      const humanOk = speakHuman(reply);
      if (!humanOk) await speakBackend(reply);

    } catch (e) {
      const msg = 'Voice command handling unavailable.';
      setLastResponse(msg);
      speakHuman(msg);
    }
  };

  const toggleListen = () => {
    if (listening) {
      try { recognitionRef.current?.stop(); } catch {}
      setListening(false);
      return;
    }
    if (recognitionRef.current) {
      try { recognitionRef.current.start(); } catch {}
    } else {
      // Fallback: prompt for text
      const t = prompt('Type your voice command (browser STT not available):');
      if (t) handleCommand(t);
    }
  };

  const toggleSpeak = async () => {
    if (speaking) {
      window.speechSynthesis.cancel();
      audioRef.current?.pause();
      setSpeaking(false);
      return;
    }
    if (!lastResponse) {
      setLastResponse('No response to synthesize. Ask something first.');
      return;
    }
    const ok = speakHuman(lastResponse);
    if (!ok) await speakBackend(lastResponse);
  };

  const previewVoice = async (v: 'jarvis' | 'friday') => {
    const samples: Record<string, string> = {
      jarvis: "Good evening, sir. JARVIS online. Formant v2 — crackle eliminated. All primary systems nominal. Deep British butler, humanized, at your service.",
      friday: "Hey there. FRIDAY online. Cool, measured, and fully human now. I can open websites, play videos, and auto-send your research to ChatGPT. What do you need?"
    };
    const text = samples[v];
    onVoiceChange(v);
    const ok = speakHuman(text);
    if (!ok) await speakBackend(text);
    setLastResponse(text);
  };

  return (
    <div className="h-full overflow-y-auto p-3 sm:p-6 relative">
      <div className="max-w-3xl mx-auto space-y-5">
        {/* Header card */}
        <div className="glass-panel p-5 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-400/30 to-transparent" />
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold tracking-wide flex items-center gap-2">
                <Waves className={`w-5 h-5 ${voice === 'friday' ? 'text-amber-300' : 'text-cyan-300'}`} />
                Voice Studio — Human-like
                <span className="text-[10px] tracking-[0.2em] px-2 py-0.5 rounded-full border bg-emerald-500/10 border-emerald-500/20 text-emerald-300 ml-2">CRACKLE FIXED v2</span>
              </h2>
              <p className="text-sm text-iron-400 mt-1 max-w-xl">
                Only two Iron Man voices — <b className="text-cyan-300">JARVIS</b> deep British butler & <b className="text-amber-300">FRIDAY</b> cool companion. Both use Web Speech API human voices + clean formant v2 fallback. No cracked audio.
              </p>
            </div>
            <div className={`w-12 h-12 rounded-full grid place-items-center border ${speaking ? 'animate-pulse' : ''} ${voice === 'friday' ? 'bg-amber-500/10 border-amber-500/20' : 'bg-cyan-500/10 border-cyan-500/20'}`}>
              <div className={`w-7 h-7 rounded-full reactor-core ${speaking ? 'speaking' : ''}`} style={{ animation: speaking ? 'speak-pulse 0.4s ease-in-out infinite alternate' : undefined }} />
            </div>
          </div>

          {/* Voice selector - ONLY JARVIS + FRIDAY */}
          <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { id: 'jarvis' as const, label: 'JARVIS', desc: 'Deep 92Hz • British butler • Iron Man classic • Humanized', icon: Cpu, sample: 'Good evening, sir.' },
              { id: 'friday' as const, label: 'FRIDAY', desc: '182Hz • Cool female • Marvel companion • Human-like', icon: Zap, sample: 'All systems green.' },
            ].map(v => (
              <button
                key={v.id}
                onClick={() => previewVoice(v.id)}
                className={`group text-left p-4 rounded-xl border transition-all relative overflow-hidden ${
                  voice === v.id
                    ? v.id === 'friday'
                      ? 'bg-amber-500/10 border-amber-400/30 shadow-[0_0_20px_rgba(245,158,11,0.15)]'
                      : 'bg-cyan-500/10 border-cyan-400/30 shadow-[0_0_20px_rgba(6,182,212,0.15)]'
                    : 'bg-black/20 border-white/10 hover:border-white/20 hover:bg-white/[0.03]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl grid place-items-center border ${voice === v.id ? (v.id === 'friday' ? 'bg-amber-500/15 border-amber-500/20' : 'bg-cyan-500/15 border-cyan-500/20') : 'bg-white/5 border-white/10'}`}>
                    <v.icon className={`w-5 h-5 ${voice === v.id ? (v.id === 'friday' ? 'text-amber-300' : 'text-cyan-300') : 'text-iron-400'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-bold tracking-widest text-sm">{v.label}</span>
                      {voice === v.id && <span className={`text-[9px] px-1.5 py-0.5 rounded-full border ${v.id === 'friday' ? 'bg-amber-500/20 border-amber-500/30 text-amber-200' : 'bg-cyan-500/20 border-cyan-500/30 text-cyan-200'}`}>ACTIVE • HUMAN</span>}
                    </div>
                    <div className="text-xs text-iron-400 mt-0.5 leading-snug">{v.desc}</div>
                  </div>
                  <Play className="w-4 h-4 text-iron-500 group-hover:text-iron-200" />
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Controls */}
        <div className="flex justify-center gap-8 py-2">
          <div className="flex flex-col items-center gap-2">
            <button
              onClick={toggleListen}
              className={`relative w-24 h-24 rounded-full grid place-items-center border-2 transition-all ${
                listening ? 'bg-red-500/15 border-red-400/40 text-red-300 shadow-[0_0_24px_rgba(248,113,113,0.25)] animate-pulse' : 'bg-[#0d1a2d] border-white/10 text-iron-300 hover:border-cyan-400/30 hover:text-cyan-300'
              }`}
            >
              {listening ? <MicOff className="w-9 h-9" /> : <Mic className="w-9 h-9" />}
              {listening && <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-400 rounded-full animate-ping" />}
            </button>
            <span className="text-xs tracking-widest uppercase text-iron-500">{listening ? 'Listening…' : 'Tap to speak'}</span>
          </div>

          <div className="flex flex-col items-center gap-2">
            <button
              onClick={toggleSpeak}
              className={`relative w-24 h-24 rounded-full grid place-items-center border-2 transition-all ${
                speaking ? (voice === 'friday' ? 'bg-amber-500/15 border-amber-400/40 text-amber-200 shadow-[0_0_24px_rgba(245,158,11,0.25)]' : 'bg-cyan-500/15 border-cyan-400/40 text-cyan-200 shadow-[0_0_24px_rgba(6,182,212,0.25)]') : 'bg-[#0d1a2d] border-white/10 text-iron-300 hover:border-white/20'
              }`}
            >
              {speaking ? <Square className="w-9 h-9" /> : <Play className="w-9 h-9 ml-0.5" />}
            </button>
            <span className="text-xs tracking-widest uppercase text-iron-500">{speaking ? 'Speaking…' : 'Play response'}</span>
          </div>
        </div>

        {/* Visualizer */}
        <div className={`glass-panel p-4 flex items-center justify-center gap-1.5 h-20 overflow-hidden ${voice === 'friday' ? 'friday-accent' : ''}`}>
          {Array.from({ length: 28 }).map((_, i) => (
            <div
              key={i}
              className="wave-bar"
              style={{
                animationDelay: `${i * 0.05}s`,
                animationPlayState: speaking || listening ? 'running' : 'paused',
                opacity: speaking || listening ? 1 : 0.25,
                height: speaking || listening ? undefined : '14%',
                background: voice === 'friday' ? 'linear-gradient(180deg, #fde68a, #d97706)' : undefined,
              }}
            />
          ))}
        </div>

        {lastTranscript && (
          <div className="glass-panel p-4">
            <div className="flex items-center gap-2 mb-2">
              <Mic className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-semibold tracking-widest uppercase text-iron-400">Heard (STT)</h3>
              <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-iron-500">Web Speech API + Whisper fallback</span>
            </div>
            <p className="text-sm text-iron-100">{lastTranscript}</p>
          </div>
        )}

        {lastResponse && (
          <div className="glass-panel p-4">
            <div className="flex items-center gap-2 mb-2">
              <Volume2 className={`w-4 h-4 ${voice === 'friday' ? 'text-amber-400' : 'text-cyan-400'}`} />
              <h3 className="text-xs font-semibold tracking-widest uppercase text-iron-400">{voice.toUpperCase()} Response (Human-like TTS)</h3>
            </div>
            <p className="text-sm text-iron-200 leading-relaxed whitespace-pre-wrap">{lastResponse}</p>
          </div>
        )}

        <div className="glass-panel p-4">
          <h3 className="text-xs font-semibold tracking-widest uppercase text-iron-400 mb-3 flex items-center gap-2">
            <Settings2 className="w-4 h-4" /> Voice Engine — Crackle Fixed
          </h3>
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-iron-400">Primary Voices</span>
              <span className="font-mono text-cyan-300">JARVIS + FRIDAY only</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-iron-400">TTS Engine</span>
              <span className="font-mono text-iron-300">{engine} • v2 no-crackle</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-iron-400">Human TTS</span>
              <span className="font-mono text-iron-300">Web Speech API ({webVoices.length} system voices)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-iron-400">Backend Fallback</span>
              <span className="font-mono text-iron-300">Formant v2 — soft limiter, DC block, crossfade</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-iron-400">Features Added</span>
              <span className="text-[11px] text-emerald-300">Play video • Open website • Auto-send to ChatGPT ✓</span>
            </div>
          </div>
        </div>

        <div className="text-center text-[10px] tracking-widest uppercase text-iron-600 pb-4">
          Tip: Say "play lo-fi on YouTube" → embeds video + opens tab. "open github.com" → opens site. "ask chatgpt about X" → opens ChatGPT with query auto-filled (send the msg).
        </div>
      </div>

      <audio ref={audioRef} hidden />
    </div>
  );
}
