interface DocumentViewerProps {
  fileUrl: string;
  fileName: string;
  onClose: () => void;
  disableInteractions?: boolean;
}

export function DocumentViewer({ fileUrl, fileName, onClose, disableInteractions = false }: DocumentViewerProps) {
  return (
    <div className="flex flex-col h-full bg-slate-900/50 border-r border-slate-800/50">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-800/50">
        <div className="w-8 h-8 rounded-lg bg-orange-500/10 flex items-center justify-center flex-shrink-0">
          <svg className="w-4 h-4 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        </div>
        <span className="text-sm text-slate-300 truncate flex-1 min-w-0">
          {fileName}
        </span>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-slate-800 transition-colors flex-shrink-0"
          title="Cerrar visor"
        >
          <svg className="w-4 h-4 text-slate-400 hover:text-slate-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* PDF iframe */}
      <iframe
        src={fileUrl}
        title={fileName}
        className="flex-1 w-full bg-white"
        style={{ pointerEvents: disableInteractions ? "none" : "auto" }}
      />
    </div>
  );
}
