import { useCallback, useEffect, useState } from "react";
import { useSpeechToText } from "../hooks/useSpeechToText";

interface ChatInputProps {
  onSend: (message: string) => void;
  loading: boolean;
}

export function ChatInput({ onSend, loading }: ChatInputProps) {
  const [input, setInput] = useState("");
  const [manualFallbackOpen, setManualFallbackOpen] = useState(false);
  const [manualFallbackText, setManualFallbackText] = useState("");

  const handleFinalResult = useCallback((finalText: string) => {
    setInput((prev) => (prev ? `${prev} ${finalText}` : finalText));
  }, []);

  const {
    interimTranscript,
    isListening,
    isSupported,
    error,
    startListening,
    stopListening,
  } = useSpeechToText({ onFinalResult: handleFinalResult });

  useEffect(() => {
    if (loading && isListening) {
      stopListening();
    }
  }, [loading, isListening, stopListening]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSend(input.trim());
    setInput("");
    setManualFallbackText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleMicClick = () => {
    if (isListening) {
      stopListening();
      return;
    }
    startListening();
  };

  const isSpeechFallbackActive = !isSupported || Boolean(error);

  const handleAppendManualFallback = () => {
    const text = manualFallbackText.trim();
    if (!text) return;
    setInput((prev) => (prev ? `${prev} ${text}` : text));
    setManualFallbackText("");
    setManualFallbackOpen(false);
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="relative bg-gradient-to-b from-slate-800 to-slate-800/90 rounded-[28px] border border-slate-700/50 focus-within:border-slate-600/70 focus-within:shadow-lg focus-within:shadow-slate-900/50 transition-all duration-300">
        {isListening && interimTranscript && (
          <p className="px-6 pt-3 pb-0 text-xs text-slate-500 italic truncate">
            {interimTranscript}
          </p>
        )}

        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Escribe tu pregunta..."
          rows={1}
          className={`w-full px-6 ${isSupported ? "pr-24" : "pr-16"} bg-transparent resize-none focus:outline-none placeholder-slate-500 text-sm flex items-center`}
          style={{
            minHeight: "60px",
            maxHeight: "200px",
            paddingTop: "20px",
            paddingBottom: "20px",
          }}
        />

        {isSupported && (
          <button
            type="button"
            onClick={handleMicClick}
            disabled={loading}
            className={`absolute right-14 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-xl transition-all duration-200 ${
              isListening
                ? "text-red-500 animate-pulse-ring"
                : "text-slate-400 hover:text-orange-500"
            } disabled:text-slate-600 disabled:cursor-not-allowed`}
            title={isListening ? "Detener grabacion" : "Iniciar grabacion de voz"}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isListening ? (
                <rect x="6" y="6" width="12" height="12" rx="2" strokeWidth={2} fill="currentColor" />
              ) : (
                <>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19v4M8 23h8" />
                </>
              )}
            </svg>
          </button>
        )}

        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="absolute right-4 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-xl bg-gradient-to-br from-orange-500 to-orange-600 hover:from-orange-400 hover:to-orange-500 disabled:from-slate-700 disabled:to-slate-700 disabled:text-slate-500 transition-all duration-200 shadow-lg hover:shadow-orange-500/25 hover:scale-105 active:scale-95"
        >
          {loading ? (
            <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          )}
        </button>
      </div>

      {error && (
        <p className="text-[11px] text-red-400 mt-2 text-center animate-pulse">
          {error}
        </p>
      )}

      {isSpeechFallbackActive && (
        <div className="mt-2 text-center">
          <button
            type="button"
            onClick={() => setManualFallbackOpen((prev) => !prev)}
            disabled={loading}
            className="text-[11px] text-amber-400/90 hover:text-amber-300 underline underline-offset-2 disabled:text-slate-500 disabled:no-underline"
          >
            {manualFallbackOpen ? "Cerrar dictado manual" : "Si voz falla, usar dictado manual"}
          </button>
        </div>
      )}

      {isSpeechFallbackActive && manualFallbackOpen && (
        <div className="mt-2 rounded-2xl border border-slate-700/70 bg-slate-900/70 p-3">
          <p className="text-[11px] text-slate-400 mb-2">
            Pega texto dictado (Windows: Win+H, macOS: Dictado, movil: teclado por voz).
          </p>
          <textarea
            value={manualFallbackText}
            onChange={(e) => setManualFallbackText(e.target.value)}
            rows={3}
            placeholder="Pega aqui el texto dictado..."
            className="w-full rounded-xl bg-slate-800/90 border border-slate-700 px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-slate-500 resize-y"
          />
          <div className="mt-2 flex justify-end">
            <button
              type="button"
              onClick={handleAppendManualFallback}
              disabled={loading || !manualFallbackText.trim()}
              className="h-8 px-3 rounded-lg text-[11px] font-semibold uppercase tracking-wide bg-slate-700 text-slate-100 hover:bg-orange-600 disabled:bg-slate-800 disabled:text-slate-500"
            >
              Agregar al mensaje
            </button>
          </div>
        </div>
      )}

      <p className="text-[11px] text-slate-600 mt-3 text-center">
        Presiona Enter para enviar
      </p>
    </form>
  );
}
