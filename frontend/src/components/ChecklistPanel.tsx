import { useState } from "react";
import type { ChecklistItem, ChecklistItemStatus, ChecklistResponse } from "../types";

const STATUS_CYCLE: ChecklistItemStatus[] = ["pending", "compliant", "non_compliant", "not_applicable"];

const STATUS_CONFIG: Record<ChecklistItemStatus, { label: string; bg: string; text: string; ring: string }> = {
  pending: { label: "Pendiente", bg: "bg-slate-700/40", text: "text-slate-400", ring: "ring-slate-600/30" },
  compliant: { label: "Cumple", bg: "bg-emerald-500/20", text: "text-emerald-400", ring: "ring-emerald-500/30" },
  non_compliant: { label: "No cumple", bg: "bg-red-500/20", text: "text-red-400", ring: "ring-red-500/30" },
  not_applicable: { label: "N/A", bg: "bg-slate-600/20", text: "text-slate-500", ring: "ring-slate-600/20" },
};

const CATEGORY_LABELS: Record<string, string> = {
  legal: "Legal",
  technical: "Tecnico",
  financial: "Financiero",
  administrative: "Administrativo",
  timeline: "Plazos",
  other: "Otro",
};

interface ChecklistPanelProps {
  checklist: ChecklistResponse | null;
  onGenerate: () => void;
  onUpdateItem: (itemId: string, status: ChecklistItemStatus) => void;
  loading: boolean;
  hasDocuments: boolean;
}

export function ChecklistPanel({ checklist, onGenerate, onUpdateItem, loading, hasDocuments }: ChecklistPanelProps) {
  const [activeFilter, setActiveFilter] = useState<string | null>(null);

  if (!checklist) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4">
        <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-slate-800/50 flex items-center justify-center">
          <svg className="w-7 h-7 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
        </div>
        <p className="text-sm text-slate-400 mb-1 text-center">Extrae requisitos automaticamente</p>
        <p className="text-xs text-slate-600 mb-5 text-center">Genera un checklist de cumplimiento a partir de los documentos cargados</p>
        <button
          onClick={onGenerate}
          disabled={!hasDocuments || loading}
          className="px-5 py-2.5 rounded-2xl text-sm font-medium transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed bg-gradient-to-r from-orange-500 to-amber-500 text-white hover:from-orange-600 hover:to-amber-600 shadow-lg shadow-orange-500/20"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Generando...
            </span>
          ) : (
            "Generar Checklist"
          )}
        </button>
        {!hasDocuments && (
          <p className="text-xs text-slate-600 mt-3 text-center">Sube documentos primero</p>
        )}
      </div>
    );
  }

  const { items, summary } = checklist;
  const compliant = summary.by_status["compliant"] || 0;
  const progressPercent = summary.total > 0 ? Math.round((compliant / summary.total) * 100) : 0;

  const filteredItems = activeFilter
    ? items.filter((item) => item.category === activeFilter)
    : items;

  const categories = Object.keys(summary.by_category);

  const handleStatusToggle = (item: ChecklistItem) => {
    const currentIdx = STATUS_CYCLE.indexOf(item.status);
    const nextStatus = STATUS_CYCLE[(currentIdx + 1) % STATUS_CYCLE.length];
    onUpdateItem(item.id, nextStatus);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Summary Header */}
      <div className="px-4 pb-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-slate-400">{compliant}/{summary.total} cumplidos</span>
          <span className="text-xs text-slate-500">{progressPercent}%</span>
        </div>
        <div className="w-full bg-slate-800/60 rounded-full h-1.5 overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-green-400 transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Severity badges */}
        <div className="flex gap-2 mt-2.5">
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-orange-500/15 text-orange-400">
            {summary.by_severity["mandatory"] || 0} obligatorios
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-400">
            {summary.by_severity["desirable"] || 0} deseables
          </span>
        </div>
      </div>

      {/* Category Filters */}
      <div className="px-4 pb-3 flex flex-wrap gap-1.5">
        <button
          onClick={() => setActiveFilter(null)}
          className={`text-[10px] px-2 py-1 rounded-full transition-all ${
            activeFilter === null
              ? "bg-orange-500/20 text-orange-400"
              : "bg-slate-800/40 text-slate-500 hover:text-slate-300"
          }`}
        >
          Todos
        </button>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveFilter(activeFilter === cat ? null : cat)}
            className={`text-[10px] px-2 py-1 rounded-full transition-all ${
              activeFilter === cat
                ? "bg-orange-500/20 text-orange-400"
                : "bg-slate-800/40 text-slate-500 hover:text-slate-300"
            }`}
          >
            {CATEGORY_LABELS[cat] || cat} ({summary.by_category[cat]})
          </button>
        ))}
      </div>

      {/* Divider */}
      <div className="mx-4 h-px bg-gradient-to-r from-transparent via-slate-700/50 to-transparent" />

      {/* Items List */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1.5">
        {filteredItems.map((item) => {
          const statusCfg = STATUS_CONFIG[item.status];
          return (
            <button
              key={item.id}
              onClick={() => handleStatusToggle(item)}
              className={`w-full text-left p-3 rounded-2xl transition-all duration-200 hover:bg-slate-800/40 ring-1 ${statusCfg.ring} ${statusCfg.bg}`}
            >
              <div className="flex items-start gap-2.5">
                {/* Status indicator */}
                <div className={`mt-0.5 w-5 h-5 rounded-lg flex-shrink-0 flex items-center justify-center ${statusCfg.bg}`}>
                  {item.status === "compliant" && (
                    <svg className="w-3 h-3 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                  {item.status === "non_compliant" && (
                    <svg className="w-3 h-3 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  )}
                  {item.status === "pending" && (
                    <div className="w-2 h-2 rounded-full bg-slate-500" />
                  )}
                  {item.status === "not_applicable" && (
                    <span className="text-[9px] text-slate-500 font-bold">N/A</span>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <p className={`text-xs leading-relaxed ${item.status === "not_applicable" ? "text-slate-500 line-through" : "text-slate-300"}`}>
                    {item.requirement_text}
                  </p>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${
                      item.severity === "mandatory"
                        ? "bg-orange-500/15 text-orange-400"
                        : "bg-blue-500/15 text-blue-400"
                    }`}>
                      {item.severity === "mandatory" ? "Obligatorio" : "Deseable"}
                    </span>
                    {item.source_page && (
                      <span className="text-[9px] text-slate-600">p.{item.source_page}</span>
                    )}
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Regenerate button */}
      <div className="p-3 border-t border-slate-800/30">
        <button
          onClick={onGenerate}
          disabled={loading}
          className="w-full text-xs text-slate-500 hover:text-slate-300 py-2 rounded-xl hover:bg-slate-800/30 transition-all disabled:opacity-40"
        >
          {loading ? "Regenerando..." : "Regenerar checklist"}
        </button>
      </div>
    </div>
  );
}
