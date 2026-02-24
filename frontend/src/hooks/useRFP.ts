import { useCallback, useState } from "react";
import type { ChatResponse, IngestResponse, UploadProgress } from "../types";

// For production: VITE_API_URL should be set to the backend URL (e.g., https://your-backend.onrender.com)
// For local dev: Falls back to empty string, using Vite's proxy configuration
const API_BASE = import.meta.env.VITE_API_URL || "";
const API_URL = `${API_BASE}/api`;

interface UseRFPReturn {
  loading: boolean;
  error: string | null;
  uploadProgress: UploadProgress | null;
  uploadDocument: (file: File) => Promise<IngestResponse | null>;
  uploadDocumentStream: (file: File) => Promise<{ chunks_processed: number } | null>;
  askQuestion: (question: string) => Promise<ChatResponse | null>;
  clearError: () => void;
}

export function useRFP(): UseRFPReturn {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);

  const apiCall = useCallback(async <T>(
    endpoint: string,
    options: RequestInit,
    errorMsg: string
  ): Promise<T | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}${endpoint}`, options);
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || errorMsg);
      }
      return await response.json();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const uploadDocument = useCallback(async (file: File): Promise<IngestResponse | null> => {
    const formData = new FormData();
    formData.append("file", file);
    return apiCall<IngestResponse>("/ingest", { method: "POST", body: formData }, "Error al subir documento");
  }, [apiCall]);

  const uploadDocumentStream = useCallback(async (file: File): Promise<{ chunks_processed: number } | null> => {
    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setError(null);
    setUploadProgress({ phase: "parsing", message: "Conectando..." });

    try {
      const response = await fetch(`${API_URL}/ingest/stream`, {
        method: "POST",
        body: formData,
      });

      // Fallback to classic endpoint if streaming is not available (404)
      if (response.status === 404) {
        setUploadProgress({ phase: "parsing", message: "Procesando documento..." });
        const fallbackForm = new FormData();
        fallbackForm.append("file", file);
        const classicResponse = await fetch(`${API_URL}/ingest`, {
          method: "POST",
          body: fallbackForm,
        });
        if (!classicResponse.ok) {
          const err = await classicResponse.json();
          throw new Error(err.detail || "Error al subir documento");
        }
        const result = await classicResponse.json();
        setUploadProgress({ phase: "done", message: "Documento procesado", chunks: result.chunks_processed });
        return { chunks_processed: result.chunks_processed };
      }

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Error al subir documento");
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("Stream no disponible");

      const decoder = new TextDecoder();
      let lastEvent: UploadProgress | null = null;
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        // Keep last incomplete line in buffer
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const event: UploadProgress = JSON.parse(line.slice(6));
              setUploadProgress(event);
              lastEvent = event;
            } catch {
              // Ignore malformed SSE lines
            }
          }
        }
      }

      if (lastEvent?.phase === "done") {
        return { chunks_processed: lastEvent.chunks || 0 };
      }
      if (lastEvent?.phase === "error") {
        throw new Error(lastEvent.message);
      }
      return null;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
      return null;
    } finally {
      setLoading(false);
      // Clear progress after a short delay so user sees the final state
      setTimeout(() => setUploadProgress(null), 2000);
    }
  }, []);

  const askQuestion = useCallback(async (question: string): Promise<ChatResponse | null> => {
    return apiCall<ChatResponse>("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }, "Error al procesar pregunta");
  }, [apiCall]);

  const clearError = useCallback(() => setError(null), []);

  return { loading, error, uploadProgress, uploadDocument, uploadDocumentStream, askQuestion, clearError };
}
