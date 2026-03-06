interface ResizeHandleProps {
  onMouseDown: (e: React.MouseEvent) => void;
}

export function ResizeHandle({ onMouseDown }: ResizeHandleProps) {
  return (
    <div
      onMouseDown={onMouseDown}
      className="w-1.5 flex-shrink-0 cursor-col-resize group relative flex items-center justify-center hover:bg-orange-500/10 transition-colors"
    >
      <div className="absolute inset-y-0 -left-1 -right-1" />
      <div className="w-px h-8 bg-slate-700 group-hover:bg-orange-500/50 transition-colors rounded-full" />
    </div>
  );
}
