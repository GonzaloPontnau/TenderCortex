import { useState } from "react";
import type { ChecklistItemStatus, ChecklistResponse, Document, UploadProgress } from "../types";
import { ChecklistPanel } from "./ChecklistPanel";
import { InfoModal } from "./InfoModal";

const PHASE_CONFIG: Record<string, { label: string; percent: number; color: string }> = {
  parsing:   { label: "Extrayendo texto",    percent: 15,  color: "from-blue-500 to-blue-400" },
  splitting: { label: "Dividiendo en chunks", percent: 30,  color: "from-cyan-500 to-cyan-400" },
  embedding: { label: "Generando embeddings", percent: 60,  color: "from-orange-500 to-amber-400" },
  indexing:  { label: "Indexando",            percent: 90,  color: "from-emerald-500 to-green-400" },
  done:      { label: "Completado",           percent: 100, color: "from-emerald-500 to-green-400" },
  error:     { label: "Error",                percent: 100, color: "from-red-500 to-red-400" },
};

interface SidebarProps {
  documents: Document[];
  onUpload: (file: File) => Promise<{ chunks_processed: number } | null>;
  loading: boolean;
  uploadProgress: UploadProgress | null;
  checklist: ChecklistResponse | null;
  onGenerateChecklist: () => void;
  onUpdateChecklistItem: (itemId: string, status: ChecklistItemStatus) => void;
  checklistLoading: boolean;
  onDocumentSelect?: (doc: Document) => void;
  activeDocumentName?: string | null;
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ documents, onUpload, loading, uploadProgress, checklist, onGenerateChecklist, onUpdateChecklistItem, checklistLoading, onDocumentSelect, activeDocumentName, isOpen = false, onClose }: SidebarProps) {
  const [dragOver, setDragOver] = useState(false);
  const [activeTab, setActiveTab] = useState<"docs" | "checklist">("docs");

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file?.name.endsWith(".pdf")) {
      await onUpload(file);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await onUpload(file);
      e.target.value = "";
    }
  };

  const phaseInfo = uploadProgress ? PHASE_CONFIG[uploadProgress.phase] : null;

  // Calculate embedding progress within its range (30% → 90%)
  const getProgressPercent = (): number => {
    if (!uploadProgress || !phaseInfo) return 0;
    if (uploadProgress.phase === "embedding" && uploadProgress.batch_total && uploadProgress.batch_current) {
      const embeddingBase = 30;
      const embeddingRange = 60; // 30% → 90%
      return embeddingBase + (uploadProgress.batch_current / uploadProgress.batch_total) * embeddingRange;
    }
    return phaseInfo.percent;
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 md:hidden"
          onClick={() => onClose?.()}
          aria-label="Cerrar panel"
        />
      )}

      <aside className={`
        fixed inset-y-0 left-0 z-40 w-72
        transition-transform duration-300 ease-in-out
        md:relative md:z-auto
        ${isOpen ? "translate-x-0" : "max-md:-translate-x-full"}
        bg-gradient-to-b from-slate-900 to-slate-900/95 border-r border-slate-800/50 flex flex-col
      `}>
      {/* Logo */}
      <div className="p-6">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="absolute inset-0 bg-orange-500/20 rounded-full blur-lg" />
            <img 
              src="/logo.png" 
              alt="TenderCortex" 
              className="relative w-11 h-11 rounded-full object-cover ring-2 ring-orange-500/30"
            />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="font-semibold text-white">TenderCortex</h1>
            <p className="text-xs text-slate-500">Multi-Agent Intelligence</p>
          </div>
          <div className="flex items-center gap-1">
            <InfoModal />
            {onClose && (
              <button
                onClick={onClose}
                className="md:hidden p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors"
                aria-label="Cerrar panel"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Divider */}
      <div className="mx-5 h-px bg-gradient-to-r from-transparent via-slate-700/50 to-transparent" />

      {/* Upload Area */}
      <div className="p-5">
        <label
          className={`block border-2 border-dashed rounded-3xl p-7 text-center cursor-pointer transition-all duration-300 ${
            dragOver
              ? "border-orange-500/70 bg-orange-500/10 scale-[1.02]"
              : "border-slate-700/50 hover:border-slate-600/70 hover:bg-slate-800/30"
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileSelect}
            className="hidden"
            disabled={loading}
          />
          {loading && uploadProgress ? (
            <div className="flex flex-col items-center gap-3">
              {uploadProgress.phase !== "done" && uploadProgress.phase !== "error" ? (
                <div className="w-10 h-10 border-2 border-orange-500/50 border-t-orange-500 rounded-full animate-spin" />
              ) : uploadProgress.phase === "done" ? (
                <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                  <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              ) : (
                <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
                  <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
              )}
              <span className="text-sm text-slate-300 font-medium">
                {uploadProgress.message}
              </span>
              <div className="w-full bg-slate-800/60 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${phaseInfo?.color || "from-orange-500 to-amber-400"} transition-all duration-500 ease-out`}
                  style={{ width: `${getProgressPercent()}%` }}
                />
              </div>
              <span className="text-[10px] text-slate-500 uppercase tracking-wider">
                {phaseInfo?.label || uploadProgress.phase}
              </span>
            </div>
          ) : loading ? (
            <div className="flex flex-col items-center gap-3">
              <div className="w-10 h-10 border-2 border-orange-500/50 border-t-orange-500 rounded-full animate-spin" />
              <span className="text-sm text-slate-400">Procesando...</span>
            </div>
          ) : (
            <>
              <div className="w-14 h-14 mx-auto mb-3 rounded-2xl bg-slate-800/50 flex items-center justify-center">
                <svg className="w-7 h-7 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <p className="text-sm text-slate-400">Arrastra un PDF aqui</p>
              <p className="text-xs text-slate-600 mt-1">o haz click para seleccionar</p>
            </>
          )}
        </label>
      </div>

      {/* Tabs */}
      {documents.length > 0 && (
        <div className="mx-5 flex rounded-xl bg-slate-800/40 p-0.5 mb-3">
          <button
            onClick={() => setActiveTab("docs")}
            className={`flex-1 text-[11px] font-medium py-1.5 rounded-lg transition-all ${
              activeTab === "docs"
                ? "bg-slate-700/60 text-slate-200"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            Documentos
          </button>
          <button
            onClick={() => setActiveTab("checklist")}
            className={`flex-1 text-[11px] font-medium py-1.5 rounded-lg transition-all ${
              activeTab === "checklist"
                ? "bg-slate-700/60 text-slate-200"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            Checklist
          </button>
        </div>
      )}

      {/* Tab Content */}
      {activeTab === "checklist" && documents.length > 0 ? (
        <div className="flex-1 overflow-hidden flex flex-col">
          <ChecklistPanel
            checklist={checklist}
            onGenerate={onGenerateChecklist}
            onUpdateItem={onUpdateChecklistItem}
            loading={checklistLoading}
            hasDocuments={documents.length > 0}
          />
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto px-4">
          <h3 className="text-[11px] font-medium text-slate-500 uppercase tracking-wider mb-3 px-2">
            Documentos ({documents.length})
          </h3>
          {documents.length === 0 ? (
            <div className="text-center py-8">
              <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-slate-800/30 flex items-center justify-center">
                <svg className="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <p className="text-sm text-slate-600">Sin documentos</p>
            </div>
          ) : (
            <ul className="space-y-2">
              {documents.map((doc, i) => {
                const isActive = activeDocumentName === doc.name;
                const canOpen = !!doc.fileUrl && !!onDocumentSelect;
                return (
                  <li
                    key={i}
                    onClick={canOpen ? () => onDocumentSelect(doc) : undefined}
                    className={`flex items-center gap-3 p-3 rounded-2xl transition-all duration-200 group ${
                      isActive
                        ? "bg-orange-500/10 ring-1 ring-orange-500/30"
                        : canOpen ? "hover:bg-slate-800/40" : ""
                    } ${canOpen ? "cursor-pointer" : "cursor-default"}`}
                  >
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-200 ${
                      isActive
                        ? "bg-gradient-to-br from-orange-500/20 to-orange-600/10"
                        : canOpen
                          ? "bg-gradient-to-br from-slate-800 to-slate-800/50 group-hover:from-orange-500/20 group-hover:to-orange-600/10"
                          : "bg-gradient-to-br from-slate-800 to-slate-800/50"
                    }`}>
                      <svg className={`w-5 h-5 transition-colors ${isActive ? "text-orange-400" : canOpen ? "text-slate-400 group-hover:text-orange-400" : "text-slate-500"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-300 truncate">{doc.name}</p>
                      <p className="text-xs text-slate-600">
                        {canOpen ? `${doc.chunks} chunks indexados` : `${doc.chunks} chunks · solo escritorio`}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}

      </aside>
    </>
  );
}
