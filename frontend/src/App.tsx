import { useRef, useState, useEffect } from "react";
import { ChatInput } from "./components/ChatInput";
import { ChatMessage } from "./components/ChatMessage";
import { PromptSuggestions } from "./components/PromptSuggestions";
import { Sidebar } from "./components/Sidebar";
import { useRFP } from "./hooks/useRFP";
import type { ChecklistItem, ChecklistItemStatus, ChecklistResponse, ChecklistSummary, Document, Message } from "./types";

function recalcSummary(items: ChecklistItem[]): ChecklistSummary {
  const by_category: Record<string, number> = {};
  const by_severity: Record<string, number> = {};
  const by_status: Record<string, number> = {};
  for (const item of items) {
    by_category[item.category] = (by_category[item.category] || 0) + 1;
    by_severity[item.severity] = (by_severity[item.severity] || 0) + 1;
    by_status[item.status] = (by_status[item.status] || 0) + 1;
  }
  return { total: items.length, by_category, by_severity, by_status };
}

// Message shown when user tries to ask without uploading documents
const NO_DOCUMENTS_MESSAGE = `**No hay documentos cargados**

Para poder responder tu pregunta, por favor:

1. **Sube uno o más documentos PDF** usando el área de carga en el panel izquierdo
2. Espera a que se procesen los documentos
3. Vuelve a hacer tu pregunta

Una vez que hayas cargado los documentos de licitación, podré analizar y responder preguntas específicas sobre su contenido.`;

export default function App() {
  const { loading, error, uploadProgress, uploadDocumentStream, askQuestion, generateChecklist, updateChecklistItem, clearError } = useRFP();
  const [messages, setMessages] = useState<Message[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [thinkingMessages, setThinkingMessages] = useState<string[]>([]);
  const [isAnswering, setIsAnswering] = useState(false);
  const [checklist, setChecklist] = useState<ChecklistResponse | null>(null);
  const [checklistLoading, setChecklistLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleUpload = async (file: File) => {
    const result = await uploadDocumentStream(file);
    if (result) {
      setDocuments((prev) => [
        ...prev,
        {
          name: file.name,
          chunks: result.chunks_processed,
          uploadedAt: new Date(),
        },
      ]);
    }
    return result;
  };

  const handleGenerateChecklist = async () => {
    setChecklistLoading(true);
    try {
      const result = await generateChecklist();
      if (result) setChecklist(result);
    } finally {
      setChecklistLoading(false);
    }
  };

  const handleUpdateChecklistItem = (itemId: string, status: ChecklistItemStatus) => {
    if (!checklist) return;
    setChecklist({
      ...checklist,
      items: checklist.items.map((item) =>
        item.id === itemId ? { ...item, status } : item
      ),
      summary: recalcSummary(checklist.items.map((item) =>
        item.id === itemId ? { ...item, status } : item
      )),
    });
    updateChecklistItem(itemId, status);
  };

  const handleSend = async (question: string) => {
    setThinkingMessages([]);

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: question,
    };
    setMessages((prev) => [...prev, userMessage]);

    // If no documents uploaded in this session, show helpful message
    if (documents.length === 0) {
      const noDocsMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: NO_DOCUMENTS_MESSAGE,
      };
      setMessages((prev) => [...prev, noDocsMessage]);
      setThinkingMessages([]);
      return;
    }

    setIsAnswering(true);
    try {
      const response = await askQuestion(question, (status) => {
        setThinkingMessages((prev) => {
          const next = [...prev, status.message];
          return next.slice(-3);
        });
      });
      if (response) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: response.answer,
          sources: response.sources,
          agentMetadata: response.agent_metadata,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    } finally {
      setIsAnswering(false);
      setThinkingMessages([]);
    }
  };

  return (
    <div className="h-screen bg-gradient-to-br from-slate-950 via-slate-950 to-slate-900 text-slate-100 flex overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        documents={documents}
        onUpload={handleUpload}
        loading={loading}
        uploadProgress={uploadProgress}
        checklist={checklist}
        onGenerateChecklist={handleGenerateChecklist}
        onUpdateChecklistItem={handleUpdateChecklistItem}
        checklistLoading={checklistLoading}
      />

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Error Banner */}
        {error && (
          <div className="mx-6 mt-5 px-5 py-4 bg-red-950/30 border border-red-900/30 rounded-2xl flex items-center justify-between backdrop-blur-sm">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-red-500/20 flex items-center justify-center">
                <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span className="text-sm text-red-300">{error}</span>
            </div>
            <button
              onClick={clearError}
              className="p-2 hover:bg-red-900/30 rounded-xl transition-colors"
            >
              <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Chat Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {messages.length === 0 ? (
            <PromptSuggestions onSelect={handleSend} />
          ) : (
            <div className="flex-1 overflow-y-auto">
              <div className="max-w-3xl mx-auto py-10 px-6 space-y-8">
                {messages.map((msg) => (
                  <ChatMessage
                    key={msg.id}
                    role={msg.role}
                    content={msg.content}
                    sources={msg.sources}
                    agentMetadata={msg.agentMetadata}
                  />
                ))}
                {loading && isAnswering && (
                  <div className="flex gap-4">
                    <div className="relative flex-shrink-0">
                      <div className="absolute inset-0 bg-orange-500/20 rounded-full blur-md animate-pulse" />
                      <img
                        src="/logo.png"
                        alt="Agent"
                        className="relative w-9 h-9 rounded-full object-cover ring-2 ring-orange-500/30"
                      />
                    </div>
                    <div className="bg-gradient-to-br from-slate-800/80 to-slate-800/60 border border-slate-700/30 rounded-3xl rounded-tl-lg px-5 py-4 shadow-lg">
                      <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
                        <span className="inline-block w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
                        <span>Razonando</span>
                      </div>
                      <div className="space-y-1">
                        {(thinkingMessages.length > 0 ? thinkingMessages : ["Analizando tu consulta..."]).map((item, idx) => (
                          <p key={`${item}-${idx}`} className="text-xs text-slate-300 leading-relaxed">
                            {item}
                          </p>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-slate-800/30 bg-gradient-to-t from-slate-900/80 to-transparent backdrop-blur-sm">
          <div className="max-w-3xl mx-auto p-6 pt-5">
            <ChatInput onSend={handleSend} loading={loading} />
          </div>
        </div>
      </main>
    </div>
  );
}
