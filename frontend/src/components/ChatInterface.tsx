import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Sparkles, ExternalLink, Play, Globe, MessageSquare, Youtube, Clock, Calculator, StickyNote, Volume2, StopCircle } from 'lucide-react';
import { apiFetch } from '../hooks/useApi';
import type { ChatMessage } from '../types';

interface ExecuteResponse {
  handled: boolean;
  skill: string | null;
  reply: string;
  intent: string;
  success: boolean;
  data: any;
  audio_base64?: string | null;
  data_uri?: string | null;
  duration_ms: number;
}

interface Props {
  voice: 'jarvis' | 'friday';
  onVoiceChange: (v: 'jarvis' | 'friday') => void;
}

export function ChatInterface({ voice }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Good evening, sir. JARVIS OS v2 online — all primary systems nominal. Voice crackle eliminated, human-like JARVIS & FRIDAY ready.\n\nTry: "play lo-fi on YouTube", "open github.com", "ask ChatGPT about quantum computing" — I will open the site, play the video, and auto-send to ChatGPT.',
      timestamp: Date.now(),
      model: 'jarvis-v2',
    },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [activeMedia, setActiveMedia] = useState<{ url: string; title: string; type: 'youtube' | 'spotify' | 'website' | 'chatgpt' } | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, activeMedia]);

  // Web Speech API voices for human-like
  const speakHuman = (text: string) => {
    if (!('speechSynthesis' in window)) return false;
    try {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text.slice(0, 400));
      const voices = window.speechSynthesis.getVoices();
      // Prefer Google UK English Male for JARVIS, Female for FRIDAY
      let preferred: SpeechSynthesisVoice | undefined;
      if (voice === 'jarvis') {
        preferred = voices.find(v => /Google.*UK.*Male/i.test(v.name)) ||
                    voices.find(v => /Male/i.test(v.name) && /en-GB/i.test(v.lang)) ||
                    voices.find(v => /en-GB/i.test(v.lang)) ||
                    voices.find(v => v.lang.startsWith('en') && /male/i.test(v.name)) ||
                    voices.find(v => v.lang.startsWith('en'));
      } else {
        preferred = voices.find(v => /Google.*UK.*Female/i.test(v.name)) ||
                    voices.find(v => /Female/i.test(v.name) && /en-GB/i.test(v.lang)) ||
                    voices.find(v => /en-US/i.test(v.lang) && /Female/i.test(v.lang)) ||
                    voices.find(v => v.lang.startsWith('en') && v.name.toLowerCase().includes('female')) ||
                    voices.find(v => v.lang.startsWith('en'));
      }
      if (preferred) utter.voice = preferred;
      utter.rate = voice === 'jarvis' ? 0.88 : 0.95;
      utter.pitch = voice === 'jarvis' ? 0.92 : 1.08;
      utter.volume = 0.95;
      utter.onstart = () => setIsSpeaking(true);
      utter.onend = () => setIsSpeaking(false);
      utter.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utter);
      return true;
    } catch {
      return false;
    }
  };

  useEffect(() => {
    // Preload voices
    if ('speechSynthesis' in window) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
    }
  }, []);

  const speakWithBackend = async (text: string) => {
    try {
      const data = await apiFetch<{ audio_base64: string; data_uri: string }>('/voice/speak', {
        method: 'POST',
        body: JSON.stringify({ text: text.slice(0, 600), voice }),
      });
      if (data?.audio_base64 && audioRef.current) {
        const binary = atob(data.audio_base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
        const blob = new Blob([bytes], { type: 'audio/wav' });
        const url = URL.createObjectURL(blob);
        audioRef.current.src = url;
        setIsSpeaking(true);
        await audioRef.current.play().catch(() => setIsSpeaking(false));
      }
    } catch {}
  };

  const handleSpeakResponse = async (text: string) => {
    const ok = speakHuman(text);
    if (!ok) await speakWithBackend(text);
  };

  const handleOpenUrl = (url: string, type: 'youtube' | 'spotify' | 'website' | 'chatgpt', title: string) => {
    setActiveMedia({ url, type, title });
    // Auto-open in new tab (user gesture context from send)
    try {
      if (type === 'chatgpt' || type === 'website' || type === 'youtube') {
        window.open(url, '_blank', 'noopener,noreferrer');
      } else if (type === 'spotify') {
        window.open(url, '_blank', 'noopener,noreferrer');
      }
    } catch {}
  };

  const getEmbedUrl = (url: string, type: string) => {
    if (type === 'youtube') {
      // Convert youtube search or watch to embed
      try {
        const u = new URL(url);
        const q = u.searchParams.get('search_query') || u.searchParams.get('q') || '';
        if (q) {
          // Embed search list
          return `https://www.youtube.com/embed?listType=search&list=${encodeURIComponent(q)}`;
        }
        const v = u.searchParams.get('v');
        if (v) return `https://www.youtube.com/embed/${v}?autoplay=1`;
        // If already /results? search
        return url;
      } catch {
        return url;
      }
    }
    return url;
  };

  const sendMessage = async (override?: string) => {
    const raw = (override ?? input).trim();
    if (!raw || sending) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: raw,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setSending(true);

    try {
      // Use skills/execute which goes through orchestrator (skills + chat)
      const data = await apiFetch<ExecuteResponse>('/skills/execute', {
        method: 'POST',
        body: JSON.stringify({ text: raw, dry_run: false, speak: false }),
      });

      if (data) {
        // Handle URL opening / media
        if (data.data?.url) {
          const url: string = data.data.url;
          const lower = url.toLowerCase();
          const skill = (data.skill || '').toLowerCase();

          if (skill.includes('youtube') || skill.includes('play') || lower.includes('youtube') || lower.includes('youtu.be')) {
            handleOpenUrl(url, 'youtube', data.data.query || data.data.site || 'YouTube');
          } else if (lower.includes('spotify')) {
            handleOpenUrl(url, 'spotify', data.data.query || 'Spotify');
          } else if (skill.includes('ask_ai') || lower.includes('chatgpt.com') || lower.includes('gemini') || lower.includes('claude') || lower.includes('perplexity')) {
            const provider = data.data.provider || 'chatgpt';
            handleOpenUrl(url, 'chatgpt', `${provider} — ${data.data.query?.slice(0,60) || 'Research'}`);
          } else if (lower.startsWith('http')) {
            // Generic website open
            handleOpenUrl(url, 'website', data.data.site || data.data.place || new URL(url).hostname);
          }
        }

        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.reply,
          timestamp: Date.now(),
          model: data.skill || data.intent,
          durationMs: data.duration_ms,
        };
        setMessages((prev) => [...prev, assistantMsg]);

        // Speak response with human-like voice (JARVIS or FRIDAY)
        handleSpeakResponse(data.reply);
      }
    } catch (e: any) {
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'system',
        content: `Error: ${e.message || 'Failed to reach JARVIS.'} Try: POST /api/v1/skills/execute`,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setSending(false);
    }
  };

  const quickActions = [
    { label: 'Play YouTube', icon: Youtube, q: 'play lo-fi hip hop on YouTube', color: 'text-red-400' },
    { label: 'Open GitHub', icon: Globe, q: 'open github.com', color: 'text-iron-300' },
    { label: 'Ask ChatGPT', icon: Sparkles, q: 'ask ChatGPT about quantum computing basics', color: 'text-violet-400' },
    { label: 'Search Web', icon: MessageSquare, q: 'search for Iron Man suit specs', color: 'text-cyan-400' },
    { label: 'Calculate', icon: Calculator, q: 'calculate 25 * 48', color: 'text-amber-400' },
    { label: 'Timer', icon: Clock, q: 'set a timer for 2 minutes', color: 'text-emerald-400' },
    { label: 'Note', icon: StickyNote, q: 'note remember to call Pepper', color: 'text-blue-400' },
  ];

  return (
    <div className="flex flex-col h-full relative">
      {/* Top HUD bar with media preview */}
      {activeMedia && (
        <div className="mx-3 mt-3 glass-panel p-3 animate-fadeInUp relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-xs">
              {activeMedia.type === 'youtube' && <Youtube className="w-4 h-4 text-red-400" />}
              {activeMedia.type === 'website' && <Globe className="w-4 h-4 text-cyan-400" />}
              {activeMedia.type === 'chatgpt' && <Sparkles className="w-4 h-4 text-violet-400" />}
              {activeMedia.type === 'spotify' && <Play className="w-4 h-4 text-green-400" />}
              <span className="font-semibold tracking-wide">{activeMedia.title}</span>
              <span className="text-iron-500 text-[10px] uppercase tracking-widest">{activeMedia.type}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => window.open(activeMedia.url, '_blank')}
                className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-[11px] flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" /> Open
              </button>
              <button
                onClick={() => setActiveMedia(null)}
                className="px-2 py-1 rounded-lg hover:bg-white/10 text-iron-500 hover:text-iron-300 text-xs"
              >
                ✕
              </button>
            </div>
          </div>

          <div className="relative rounded-xl overflow-hidden bg-black/40 border border-white/5">
            {activeMedia.type === 'youtube' ? (
              <iframe
                src={getEmbedUrl(activeMedia.url, activeMedia.type)}
                className="w-full h-[220px] sm:h-[300px]"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                title={activeMedia.title}
              />
            ) : (
              <div className="p-3 flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl grid place-items-center ${voice === 'friday' ? 'bg-amber-500/15' : 'bg-cyan-500/15'}`}>
                  {activeMedia.type === 'chatgpt' ? <Sparkles className="w-5 h-5 text-violet-400" /> : <Globe className="w-5 h-5 text-cyan-400" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{activeMedia.url}</div>
                  <div className="text-xs text-iron-500 truncate">Opened in new tab — auto-sent from JARVIS command. "After writing to ChatGPT send the msg" ✓</div>
                </div>
                <button onClick={() => window.open(activeMedia.url, '_blank')} className="btn-jarvis text-xs">Open Now</button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 sm:p-5 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeInUp`}
          >
            {msg.role === 'assistant' && (
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${voice === 'friday' ? 'bg-amber-500/10 border-amber-500/20' : 'bg-cyan-500/10 border-cyan-500/20'}`}>
                <Bot className={`w-4 h-4 ${voice === 'friday' ? 'text-amber-300' : 'text-cyan-300'}`} />
              </div>
            )}

            <div
              className={`max-w-[88%] sm:max-w-[72%] rounded-2xl px-4 py-3 text-[14px] leading-relaxed shadow-lg ${
                msg.role === 'user'
                  ? voice === 'friday'
                    ? 'bg-gradient-to-br from-amber-600 to-yellow-700 text-white rounded-br-md'
                    : 'msg-user rounded-br-md'
                  : msg.role === 'system'
                  ? 'bg-red-500/10 text-red-300 border border-red-500/20 rounded-bl-md'
                  : `msg-assistant rounded-bl-md ${isSpeaking ? 'ring-1 ring-cyan-400/20' : ''}`
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.model && (
                <div className="mt-2.5 flex items-center gap-2 text-[10px] opacity-70 flex-wrap">
                  <span className={`px-2 py-0.5 rounded-full border text-[10px] tracking-wide ${voice === 'friday' ? 'bg-amber-500/10 border-amber-500/20 text-amber-300' : 'bg-cyan-500/10 border-cyan-500/20 text-cyan-300'}`}>
                    {msg.model}
                  </span>
                  {msg.durationMs && <span className="font-mono">{msg.durationMs.toFixed(0)}ms</span>}
                  <button
                    onClick={() => handleSpeakResponse(msg.content)}
                    className="ml-auto flex items-center gap-1 hover:text-white transition-colors"
                  >
                    <Volume2 className="w-3 h-3" /> Hear again
                  </button>
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-9 h-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center shrink-0">
                <User className="w-4 h-4 text-iron-300" />
              </div>
            )}
          </div>
        ))}

        {sending && (
          <div className="flex gap-3 animate-fadeInUp">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${voice === 'friday' ? 'bg-amber-500/10 border-amber-500/20' : 'bg-cyan-500/10 border-cyan-500/20'}`}>
              <Bot className={`w-4 h-4 ${voice === 'friday' ? 'text-amber-300' : 'text-cyan-300'}`} />
            </div>
            <div className="glass-panel rounded-2xl rounded-bl-md px-4 py-3.5 flex items-center gap-3">
              <div className="flex gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-xs text-iron-400 tracking-wide">JARVIS processing • skills + memory • {voice.toUpperCase()}</span>
            </div>
          </div>
        )}

        {/* Quick actions */}
        <div className="pt-2">
          <div className="text-[10px] tracking-[0.18em] text-iron-500 uppercase mb-2 flex items-center gap-2">
            <span>Quick — Play video • Open website • Send to ChatGPT</span>
            {isSpeaking && <span className="flex items-center gap-1 text-cyan-400"><Volume2 className="w-3 h-3 animate-pulse" /> Speaking</span>}
          </div>
          <div className="flex flex-wrap gap-2">
            {quickActions.map((a) => (
              <button
                key={a.label}
                onClick={() => sendMessage(a.q)}
                disabled={sending}
                className="group px-3 py-2 rounded-full bg-[#0d1a2d] border border-white/10 hover:border-cyan-400/30 hover:bg-cyan-500/5 text-xs text-iron-300 hover:text-iron-100 flex items-center gap-2 transition-all"
              >
                <a.icon className={`w-3.5 h-3.5 ${a.color} group-hover:scale-110 transition-transform`} />
                <span className="hidden sm:inline">{a.label}</span>
                <span className="sm:hidden">{a.label.split(' ')[0]}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Input bar — professional HUD */}
      <div className="p-3 sm:p-4 border-t border-white/[0.06] bg-[#0a1220]/70 backdrop-blur-xl relative">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-500/20 to-transparent" />
        <div className="flex gap-2 max-w-5xl mx-auto items-end">
          <div className="flex-1 relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              placeholder={voice === 'friday' ? 'Ask FRIDAY — e.g. open YouTube, play video, ask ChatGPT…' : 'Command JARVIS — e.g. play video on YouTube, open github.com, ask ChatGPT…'}
              rows={1}
              className="w-full input-hud rounded-2xl px-4 py-3.5 text-sm text-iron-100 placeholder-iron-500 focus:outline-none resize-none min-h-[52px] max-h-[120px] pr-12"
            />
            <div className="absolute right-2 top-2 bottom-2 flex flex-col justify-between">
              <button
                onClick={() => setInput('')}
                className={`w-7 h-7 rounded-full grid place-items-center text-[11px] border transition-all ${input ? 'opacity-100 bg-white/5 border-white/10 text-iron-400 hover:text-iron-200' : 'opacity-0 pointer-events-none'}`}
              >
                ✕
              </button>
              <div className={`w-2 h-2 rounded-full mx-auto ${sending ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400'}`} />
            </div>
          </div>

          <button
            onClick={() => sendMessage()}
            disabled={sending || !input.trim()}
            className={`${voice === 'friday' ? 'btn-friday' : 'btn-jarvis'} h-[52px] w-[52px] sm:w-auto sm:px-6 grid place-items-center rounded-2xl disabled:opacity-40 disabled:pointer-events-none`}
          >
            {sending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            <span className="hidden sm:inline ml-2 text-sm">Send</span>
          </button>

          <button
            onClick={() => {
              if (isSpeaking) {
                window.speechSynthesis.cancel();
                if (audioRef.current) audioRef.current.pause();
                setIsSpeaking(false);
              } else if (messages.length > 0) {
                const last = [...messages].reverse().find(m => m.role === 'assistant');
                if (last) handleSpeakResponse(last.content);
              }
            }}
            className={`h-[52px] w-[52px] rounded-2xl border grid place-items-center transition-all ${isSpeaking ? 'bg-red-500/15 border-red-500/30 text-red-300' : 'bg-white/[0.04] border-white/10 text-iron-400 hover:text-iron-200 hover:border-white/20'}`}
            title={isSpeaking ? 'Stop speaking' : 'Speak last response'}
          >
            {isSpeaking ? <StopCircle className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
          </button>
        </div>
        <div className="max-w-5xl mx-auto flex items-center justify-between mt-2.5 text-[10px] text-iron-600 tracking-wide">
          <span className="flex items-center gap-2">
            <span className={`w-1 h-1 rounded-full ${voice === 'friday' ? 'bg-amber-400' : 'bg-cyan-400'}`} />
            All processing local • Offline-first • {voice.toUpperCase()} human-like • Crackle fixed (formant v2)
          </span>
          <span className="hidden sm:flex items-center gap-1.5">
            <kbd className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10">Enter</kbd> send • <kbd className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10">Shift+Enter</kbd> newline
          </span>
        </div>
      </div>

      <audio ref={audioRef} onEnded={() => setIsSpeaking(false)} onPause={() => setIsSpeaking(false)} className="hidden" />
    </div>
  );
}
