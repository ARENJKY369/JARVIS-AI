import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Sparkles } from 'lucide-react';
import { apiFetch } from '../hooks/useApi';
import type { ChatMessage } from '../types';

interface ChatResponse {
  response: string;
  model_used: string;
  duration_ms: number;
  tokens_used?: number;
  success: boolean;
}

export function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Good evening, sir. JARVIS is online and fully operational. How may I assist you today?',
      timestamp: Date.now(),
      model: 'jarvis-core',
    },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || sending) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input.trim(),
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setSending(true);

    try {
      const data = await apiFetch<ChatResponse>('/ai/chat', {
        method: 'POST',
        body: JSON.stringify({ message: userMsg.content }),
      });

      if (data) {
        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.response,
          timestamp: Date.now(),
          model: data.model_used,
          durationMs: data.duration_ms,
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } else {
        throw new Error('No response from AI service');
      }
    } catch (e: any) {
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'system',
        content: `Error: ${e.message || 'Failed to reach JARVIS AI engine.'}`,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-lg bg-jarvis-500/10 flex items-center justify-center shrink-0 border border-jarvis-500/20">
                <Bot className="w-4 h-4 text-jarvis-400" />
              </div>
            )}

            <div
              className={`max-w-[80%] sm:max-w-[70%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-jarvis-600 text-white rounded-br-md'
                  : msg.role === 'system'
                  ? 'bg-red-500/10 text-red-300 border border-red-500/20 rounded-bl-md'
                  : 'bg-iron-800 text-iron-100 border border-iron-700 rounded-bl-md'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.model && (
                <div className="mt-2 flex items-center gap-1.5 text-[10px] opacity-60">
                  <Sparkles className="w-3 h-3" />
                  <span>{msg.model}</span>
                  {msg.durationMs && <span>• {(msg.durationMs).toFixed(0)}ms</span>}
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-lg bg-iron-700 flex items-center justify-center shrink-0">
                <User className="w-4 h-4 text-iron-300" />
              </div>
            )}
          </div>
        ))}

        {sending && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-lg bg-jarvis-500/10 flex items-center justify-center shrink-0 border border-jarvis-500/20">
              <Bot className="w-4 h-4 text-jarvis-400" />
            </div>
            <div className="bg-iron-800 border border-iron-700 rounded-2xl rounded-bl-md px-4 py-3">
              <Loader2 className="w-4 h-4 animate-spin text-jarvis-400" />
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-iron-800 bg-iron-900/50">
        <div className="flex gap-2 max-w-4xl mx-auto">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask JARVIS anything..."
            rows={1}
            className="flex-1 bg-iron-800 border border-iron-700 rounded-xl px-4 py-3 text-sm text-iron-100 placeholder-iron-500 focus:outline-none focus:ring-2 focus:ring-jarvis-500/50 focus:border-jarvis-500 resize-none min-h-[44px] max-h-[120px]"
          />
          <button
            onClick={sendMessage}
            disabled={sending || !input.trim()}
            className="shrink-0 bg-jarvis-600 hover:bg-jarvis-500 disabled:bg-iron-700 disabled:text-iron-500 text-white rounded-xl px-4 py-2 transition-colors flex items-center justify-center"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-center text-[10px] text-iron-600 mt-2">
          All processing is local. No data leaves your machine.
        </p>
      </div>
    </div>
  );
}
