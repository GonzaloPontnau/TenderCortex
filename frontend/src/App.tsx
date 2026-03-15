import { useRef, useState, useEffect } from "react";
import { ChatInput } from "./components/ChatInput";
import { ChatMessage } from "./components/ChatMessage";
import { DocumentViewer } from "./components/DocumentViewer";
import { PromptSuggestions } from "./components/PromptSuggestions";
import { ResizeHandle } from "./components/ResizeHandle";
import { Sidebar } from "./components/Sidebar";
import { useMediaQuery } from "./hooks/useMediaQuery";
import { useResizePanel } from "./hooks/useResizePanel";
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
  const [activeDocument, setActiveDocument] = useState<Document | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const splitContainerRef = useRef<HTMLDivElement>(null);
  const isDesktop = useMediaQuery("(min-width: 768px)");
  const { leftPercent, isDragging, handleMouseDown, resetRatio } = useResizePanel({
    containerRef: splitContainerRef,
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!isDesktop && activeDocument) {
      setActiveDocument(null);
    }
  }, [isDesktop, activeDocument]);

  useEffect(() => {
    if (isDesktop) setIsSidebarOpen(false);
  }, [isDesktop]);

  const handleCloseViewer = () => {
    setActiveDocument(null);
    resetRatio();
  };

  const handleDocumentSelect = (doc: Document) => {
    if (doc.fileUrl) setActiveDocument(doc);
  };

  const handleUpload = async (file: File) => {
    const fileUrl = URL.createObjectURL(file);
    const result = await uploadDocumentStream(file);
    if (result) {
      setDocuments((prev) => [
        ...prev,
        {
          name: file.name,
          chunks: result.chunks_processed,
          uploadedAt: new Date(),
          fileUrl,
        },
      ]);
    } else {
      URL.revokeObjectURL(fileUrl);
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

  const handleUpdateChecklistItem = async (itemId: string, status: ChecklistItemStatus) => {
    if (!checklist) return;
    const previousItem = checklist.items.find((item) => item.id === itemId);
    if (!previousItem || previousItem.status === status) return;

    const updatedItems = checklist.items.map((item) =>
      item.id === itemId ? { ...item, status } : item
    );
    setChecklist({ ...checklist, items: updatedItems, summary: recalcSummary(updatedItems) });

    const ok = await updateChecklistItem(itemId, status);
    if (!ok) {
      const revertedItems = checklist.items.map((item) =>
        item.id === itemId ? { ...item, status: previousItem.status } : item
      );
      setChecklist({ ...checklist, items: revertedItems, summary: recalcSummary(revertedItems) });
    }
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
        onDocumentSelect={isDesktop ? handleDocumentSelect : undefined}
        activeDocumentName={activeDocument?.name ?? null}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* Main Content */}
      {activeDocument?.fileUrl && isDesktop ? (
        <div ref={splitContainerRef} className="flex-1 flex min-w-0 overflow-hidden">
          {/* Document Viewer */}
          <div className="overflow-hidden" style={{ width: `${leftPercent}%` }}>
            <DocumentViewer
              fileUrl={activeDocument.fileUrl}
              fileName={activeDocument.name}
              onClose={handleCloseViewer}
              disableInteractions={isDragging}
            />
          </div>

          <ResizeHandle onMouseDown={handleMouseDown} />

          {/* Chat Panel (split mode) */}
          <div className="flex flex-col min-w-0 overflow-hidden" style={{ width: `${100 - leftPercent}%` }}>
            {error && (
              <div className="mx-4 mt-4 px-4 py-3 bg-red-950/30 border border-red-900/30 rounded-2xl flex items-center justify-between backdrop-blur-sm">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-red-500/20 flex items-center justify-center">
                    <svg className="w-3.5 h-3.5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <span className="text-xs text-red-300">{error}</span>
                </div>
                <button onClick={clearError} className="p-1.5 hover:bg-red-900/30 rounded-lg transition-colors">
                  <svg className="w-3.5 h-3.5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            )}

            <div className="flex-1 overflow-y-auto">
              <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
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
                  <div className="flex gap-3">
                    <div className="relative flex-shrink-0">
                      <div className="absolute inset-0 bg-orange-500/20 rounded-full blur-md animate-pulse" />
                      <img src="/logo.png" alt="Agent" className="relative w-8 h-8 rounded-full object-cover ring-2 ring-orange-500/30" />
                    </div>
                    <div className="bg-gradient-to-br from-slate-800/80 to-slate-800/60 border border-slate-700/30 rounded-3xl rounded-tl-lg px-4 py-3 shadow-lg">
                      <div className="flex items-center gap-2 text-xs text-slate-400 mb-1.5">
                        <span className="inline-block w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
                        <span>Razonando</span>
                      </div>
                      <div className="space-y-1">
                        {(thinkingMessages.length > 0 ? thinkingMessages : ["Analizando tu consulta..."]).map((item, idx) => (
                          <p key={`${item}-${idx}`} className="text-xs text-slate-300 leading-relaxed">{item}</p>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>

            <div className="border-t border-slate-800/30 bg-gradient-to-t from-slate-900/80 to-transparent backdrop-blur-sm">
              <div className="max-w-2xl mx-auto p-4 pt-3">
                <ChatInput onSend={handleSend} loading={loading} />
              </div>
            </div>
          </div>
        </div>
      ) : (
        <main className="flex-1 flex flex-col min-w-0">
          {/* Mobile top bar */}
          <div className="md:hidden flex items-center gap-3 px-4 py-3 border-b border-slate-800/40">
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors"
              aria-label="Abrir panel"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="flex items-center gap-2">
              <img src="/logo.png" alt="TenderCortex" className="w-6 h-6 rounded-full object-cover ring-1 ring-orange-500/30" />
              <span className="text-sm font-medium text-slate-200">TenderCortex</span>
            </div>
          </div>

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

          <div className="flex-1 flex flex-col overflow-hidden">
            {messages.length === 0 ? (
              <PromptSuggestions onSelect={handleSend} />
            ) : (
              <div className="flex-1 overflow-y-auto">
                <div className="max-w-3xl mx-auto py-4 px-3 sm:py-10 sm:px-6 space-y-4 sm:space-y-8">
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

          <div className="border-t border-slate-800/30 bg-gradient-to-t from-slate-900/80 to-transparent backdrop-blur-sm">
            <div className="max-w-3xl mx-auto p-3 sm:p-6 sm:pt-5">
              <ChatInput onSend={handleSend} loading={loading} />
            </div>
          </div>
        </main>
      )}
    </div>
  );
}
