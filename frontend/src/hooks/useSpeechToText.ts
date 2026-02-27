import { useCallback, useEffect, useRef, useState } from "react";

interface SpeechRecognitionEvent extends Event {
  readonly resultIndex: number;
  readonly results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent extends Event {
  readonly error: string;
  readonly message: string;
}

interface SpeechRecognition extends EventTarget {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

export interface UseSpeechToTextOptions {
  lang?: string;
  interimResults?: boolean;
  continuous?: boolean;
  onFinalResult?: (finalText: string) => void;
}

export interface UseSpeechToTextReturn {
  transcript: string;
  interimTranscript: string;
  isListening: boolean;
  isSupported: boolean;
  error: string | null;
  startListening: () => void;
  stopListening: () => void;
  resetTranscript: () => void;
}

const getIsSupported = (): boolean =>
  typeof window !== "undefined" &&
  (typeof window.SpeechRecognition !== "undefined" ||
    typeof window.webkitSpeechRecognition !== "undefined");

const getSpeechRecognitionCtor = (): (new () => SpeechRecognition) | null => {
  if (typeof window === "undefined") return null;
  return window.SpeechRecognition ?? window.webkitSpeechRecognition ?? null;
};

const isSecureSpeechContext = (): boolean => {
  if (typeof window === "undefined") return false;
  if (window.isSecureContext) return true;

  const hostname = window.location.hostname;
  return hostname === "localhost" || hostname === "127.0.0.1";
};

const isLikelyBrave = (): boolean => {
  if (typeof navigator === "undefined") return false;
  return navigator.userAgent.includes("Brave");
};

export function useSpeechToText(
  options?: UseSpeechToTextOptions
): UseSpeechToTextReturn {
  const {
    lang = "es-ES",
    interimResults = true,
    continuous = false,
    onFinalResult,
  } = options ?? {};

  const onFinalResultRef = useRef(onFinalResult);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const mountedRef = useRef(true);
  const manualStopRef = useRef(false);

  const isSupported = getIsSupported();

  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    onFinalResultRef.current = onFinalResult;
  }, [onFinalResult]);

  const startListening = useCallback(() => {
    if (!isSupported || isListening) return;

    if (!isSecureSpeechContext()) {
      setError(
        "El reconocimiento de voz requiere HTTPS (o localhost) en este navegador"
      );
      return;
    }

    const Ctor = getSpeechRecognitionCtor();
    if (!Ctor) return;

    const recognition = new Ctor();
    recognition.lang = lang;
    recognition.interimResults = interimResults;
    recognition.continuous = continuous;

    setTranscript("");
    setInterimTranscript("");
    setError(null);
    manualStopRef.current = false;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      if (!mountedRef.current) return;

      let finalText = "";
      let interim = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalText += result[0].transcript;
        } else {
          interim += result[0].transcript;
        }
      }

      if (finalText) {
        setTranscript((prev) => prev + finalText);
        onFinalResultRef.current?.(finalText);
      }

      setInterimTranscript(interim);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (!mountedRef.current) return;

      if (manualStopRef.current && event.error === "aborted") {
        return;
      }

      let message: string;
      switch (event.error) {
        case "not-allowed":
          message = "Permiso de microfono denegado";
          break;
        case "service-not-allowed":
          message = "Servicio de reconocimiento de voz no disponible";
          break;
        case "audio-capture":
          message = "No se encontro un microfono disponible";
          break;
        case "network":
          if (!navigator.onLine) {
            message = "Sin conexion a internet. No se puede usar voz en este momento";
            break;
          }

          if (isLikelyBrave()) {
            message =
              "Brave bloqueo el servicio de voz. Baja Shields para este sitio o usa Chrome/Edge";
            break;
          }

          message =
            "Fallo de red del servicio de voz del navegador. Intenta nuevamente o usa Chrome/Edge";
          break;
        case "no-speech":
          message = "No se detecto voz";
          break;
        case "aborted":
          message = "Reconocimiento de voz interrumpido";
          break;
        default:
          message = `Error de reconocimiento de voz: ${event.error}`;
      }

      setError(message);
      setIsListening(false);
      setInterimTranscript("");
      recognitionRef.current = null;
    };

    recognition.onend = () => {
      if (!mountedRef.current) return;
      setIsListening(false);
      setInterimTranscript("");
      recognitionRef.current = null;
    };

    recognitionRef.current = recognition;

    try {
      recognition.start();
      setIsListening(true);
    } catch {
      recognitionRef.current = null;
      setIsListening(false);
      setError(
        "No se pudo iniciar el reconocimiento de voz. Intenta nuevamente"
      );
    }
  }, [continuous, interimResults, isListening, isSupported, lang]);

  const stopListening = useCallback(() => {
    if (!isListening || !recognitionRef.current) return;
    manualStopRef.current = true;
    recognitionRef.current.stop();
    setIsListening(false);
  }, [isListening]);

  const resetTranscript = useCallback(() => {
    setTranscript("");
    setInterimTranscript("");
    setError(null);
  }, []);

  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;
      if (recognitionRef.current) {
        recognitionRef.current.abort();
        recognitionRef.current = null;
      }
    };
  }, []);

  return {
    transcript,
    interimTranscript,
    isListening,
    isSupported,
    error,
    startListening,
    stopListening,
    resetTranscript,
  };
}
