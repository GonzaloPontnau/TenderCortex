import { useState, useEffect } from "react";

const SECTIONS = [
  {
    title: "Que es TenderCortex?",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    content: (
      <>
        <p>
          TenderCortex es un sistema de <strong className="text-orange-400">inteligencia artificial multi-agente</strong> que
          analiza documentos de licitaciones publicas automaticamente.
        </p>
        <p className="mt-2">
          Sube tu pliego o documento de licitacion en PDF y hacele preguntas en lenguaje natural.
          Agentes especializados en distintos dominios (legal, financiero, tecnico, etc.) colaboran
          para darte respuestas precisas basadas en el contenido del documento.
        </p>
      </>
    ),
  },
  {
    title: "Como funciona?",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    content: (
      <ol className="space-y-3">
        {[
          { step: "Subi tu PDF", desc: "Arrastra o selecciona el documento de licitacion en el panel izquierdo." },
          { step: "Hace tu pregunta", desc: "Escribi o dicta lo que necesitas saber sobre el documento." },
          { step: "Recibe analisis experto", desc: "El sistema detecta el dominio de tu pregunta y activa al agente especialista adecuado." },
        ].map((item, i) => (
          <li key={i} className="flex gap-3">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-orange-500/20 text-orange-400 text-xs font-bold flex items-center justify-center">
              {i + 1}
            </span>
            <div>
              <span className="text-slate-200 font-medium">{item.step}</span>
              <span className="text-slate-400 ml-1">— {item.desc}</span>
            </div>
          </li>
        ))}
      </ol>
    ),
  },
  {
    title: "Risk Sentinel",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
    content: (
      <>
        <p>
          <strong className="text-orange-400">Risk Sentinel</strong> es el agente de compliance que revisa
          automaticamente cada respuesta antes de entregarla.
        </p>
        <p className="mt-2">
          Evalua el nivel de riesgo y el estado de cumplimiento, y si detecta problemas
          los detalla para que puedas tomar decisiones informadas. Veras sus badges en cada
          respuesta del asistente.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="px-2.5 py-1 rounded-full text-[11px] font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
            Riesgo bajo
          </span>
          <span className="px-2.5 py-1 rounded-full text-[11px] font-medium bg-amber-500/15 text-amber-400 border border-amber-500/20">
            Riesgo medio
          </span>
          <span className="px-2.5 py-1 rounded-full text-[11px] font-medium bg-red-500/15 text-red-400 border border-red-500/20">
            Riesgo alto
          </span>
        </div>
      </>
    ),
  },
  {
    title: "Checklist de Cumplimiento",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
      </svg>
    ),
    content: (
      <p>
        Una vez cargado tu documento, podes generar un <strong className="text-orange-400">checklist automatico</strong> desde
        la pestana "Checklist" en el panel izquierdo. El sistema identifica los requisitos clave del pliego y te permite
        marcar cada item como cumplido, no cumplido o no aplica, para que lleves un control organizado de tu propuesta.
      </p>
    ),
  },
];

export function InfoModal() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open]);

  return (
    <>
      {/* Trigger */}
      <button
        onClick={() => setOpen(true)}
        className="w-8 h-8 rounded-xl bg-slate-800/60 border border-slate-700/40 flex items-center justify-center text-slate-500 hover:text-orange-400 hover:border-orange-500/30 hover:bg-orange-500/10 transition-all duration-200"
        title="Como funciona TenderCortex"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>

      {/* Overlay + Modal */}
      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={() => setOpen(false)}
        >
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

          <div
            className="relative w-full max-w-lg max-h-[85vh] overflow-hidden rounded-3xl bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-700/40 shadow-2xl shadow-black/40 flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="sticky top-0 z-10 bg-gradient-to-b from-slate-900 via-slate-900 to-slate-900/80 backdrop-blur-sm px-7 pt-7 pb-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div className="absolute inset-0 bg-orange-500/20 rounded-full blur-md" />
                  <img
                    src="/logo.png"
                    alt="TenderCortex"
                    className="relative w-9 h-9 rounded-full object-cover ring-2 ring-orange-500/30"
                  />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-white">TenderCortex</h2>
                  <p className="text-[11px] text-slate-500">Guia rapida</p>
                </div>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="p-2 rounded-xl hover:bg-slate-800/60 transition-colors text-slate-500 hover:text-slate-300"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Sections */}
            <div className="px-7 pb-7 space-y-6 overflow-y-auto">
              {SECTIONS.map((section) => (
                <div
                  key={section.title}
                  className="p-5 rounded-2xl bg-slate-800/30 border border-slate-700/20"
                >
                  <div className="flex items-center gap-2.5 mb-3 text-orange-400">
                    {section.icon}
                    <h3 className="text-sm font-semibold">{section.title}</h3>
                  </div>
                  <div className="text-sm text-slate-400 leading-relaxed">
                    {section.content}
                  </div>
                </div>
              ))}

              {/* Keyboard hint */}
              <p className="text-center text-[11px] text-slate-600">
                Presiona <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700/50 text-slate-400 font-mono text-[10px]">Esc</kbd> para cerrar
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
