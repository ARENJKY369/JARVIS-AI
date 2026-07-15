import { useState } from 'react';
import { Mic, MicOff, Volume2, Play, Square } from 'lucide-react';
import { apiFetch } from '../hooks/useApi';

export function VoiceControl() {
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [lastTranscript, setLastTranscript] = useState('');
  const [lastResponse, setLastResponse] = useState('');

  const toggleListen = async () => {
    if (listening) {
      setListening(false);
      return;
    }

    setListening(true);
    // Simulate transcription then send to AI
    try {
      const data = await apiFetch<{ text: string }>('/voice', {
        method: 'POST',
        body: JSON.stringify({ action: 'transcribe', audio_base64: 'dummy' }),
      });

      if (data?.text) {
        setLastTranscript(data.text);
        const chat = await apiFetch<{ response: string }>('/ai/chat', {
          method: 'POST',
          body: JSON.stringify({ message: data.text }),
        });
        if (chat?.response) {
          setLastResponse(chat.response);
        }
      }
    } catch (e) {
      setLastTranscript('Voice transcription unavailable in fallback mode.');
    } finally {
      setListening(false);
    }
  };

  const toggleSpeak = async () => {
    if (speaking) {
      setSpeaking(false);
      return;
    }

    if (!lastResponse) {
      setLastResponse('No response to synthesize. Start a conversation first.');
      return;
    }

    setSpeaking(true);
    try {
      await apiFetch('/voice', {
        method: 'POST',
        body: JSON.stringify({ action: 'synthesize', text: lastResponse }),
      });
    } catch (e) {
      // Fallback: just show it
    }
    setTimeout(() => setSpeaking(false), 2000);
  };

  return (
    <div className="h-full overflow-y-auto p-4 sm:p-6">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-iron-100">Voice Interface</h2>
          <p className="text-sm text-iron-400 mt-1">
            Speak to JARVIS or have him read responses aloud.
          </p>
        </div>

        <div className="flex justify-center gap-6">
          <button
            onClick={toggleListen}
            className={`relative w-20 h-20 rounded-full flex items-center justify-center transition-all ${
              listening
                ? 'bg-red-500/20 text-red-400 border-2 border-red-500 animate-pulse'
                : 'bg-iron-800 text-iron-300 border-2 border-iron-700 hover:border-jarvis-500 hover:text-jarvis-400'
            }`}
          >
            {listening ? <MicOff className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
          </button>

          <button
            onClick={toggleSpeak}
            className={`relative w-20 h-20 rounded-full flex items-center justify-center transition-all ${
              speaking
                ? 'bg-jarvis-500/20 text-jarvis-400 border-2 border-jarvis-500 animate-pulse'
                : 'bg-iron-800 text-iron-300 border-2 border-iron-700 hover:border-jarvis-500 hover:text-jarvis-400'
            }`}
          >
            {speaking ? <Square className="w-8 h-8" /> : <Play className="w-8 h-8" />}
          </button>
        </div>

        <div className="text-center text-xs text-iron-500">
          {listening ? 'Listening... (fallback mode)' : 'Tap microphone to speak'}
        </div>

        {lastTranscript && (
          <div className="bg-iron-900 border border-iron-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Mic className="w-4 h-4 text-jarvis-400" />
              <h3 className="text-xs font-medium text-iron-400 uppercase tracking-wider">Transcript</h3>
            </div>
            <p className="text-sm text-iron-200">{lastTranscript}</p>
          </div>
        )}

        {lastResponse && (
          <div className="bg-iron-900 border border-iron-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Volume2 className="w-4 h-4 text-jarvis-400" />
              <h3 className="text-xs font-medium text-iron-400 uppercase tracking-wider">JARVIS Response</h3>
            </div>
            <p className="text-sm text-iron-200">{lastResponse}</p>
          </div>
        )}

        <div className="bg-iron-900/50 border border-iron-800 rounded-xl p-4">
          <h3 className="text-xs font-medium text-iron-400 uppercase tracking-wider mb-3">Voice Settings</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-iron-300">Voice Profile</span>
              <span className="text-iron-500 font-mono">jarvis</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-iron-300">STT Engine</span>
              <span className="text-iron-500 font-mono">faster-whisper (fallback)</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-iron-300">TTS Engine</span>
              <span className="text-iron-500 font-mono">piper-tts (fallback)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
