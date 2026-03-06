import { useCallback, useEffect, useRef, useState } from "react";

interface UseResizePanelOptions {
  containerRef: React.RefObject<HTMLDivElement | null>;
  minLeftPx?: number;
  minRightPx?: number;
  initialPercent?: number;
}

interface UseResizePanelReturn {
  leftPercent: number;
  isDragging: boolean;
  handleMouseDown: (e: React.MouseEvent) => void;
  resetRatio: () => void;
}

export function useResizePanel({
  containerRef,
  minLeftPx = 300,
  minRightPx = 350,
  initialPercent = 50,
}: UseResizePanelOptions): UseResizePanelReturn {
  const [leftPercent, setLeftPercent] = useState(initialPercent);
  const [isDragging, setIsDragging] = useState(false);
  const leftPercentRef = useRef(leftPercent);
  useEffect(() => { leftPercentRef.current = leftPercent; }, [leftPercent]);
  const drag = useRef<{ startX: number; startPct: number } | null>(null);
  const pendingPctRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);
  const fnsRef = useRef<{ move: (e: MouseEvent) => void; up: () => void }>(null);

  const scheduleUpdate = useCallback((nextPct: number) => {
    pendingPctRef.current = nextPct;
    if (rafRef.current !== null) return;
    rafRef.current = window.requestAnimationFrame(() => {
      rafRef.current = null;
      if (pendingPctRef.current === null) return;
      setLeftPercent(pendingPctRef.current);
      pendingPctRef.current = null;
    });
  }, []);

  const cleanup = useCallback(() => {
    drag.current = null;
    setIsDragging(false);
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
    if (rafRef.current !== null) {
      window.cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    if (pendingPctRef.current !== null) {
      setLeftPercent(pendingPctRef.current);
      pendingPctRef.current = null;
    }
    if (fnsRef.current) {
      window.removeEventListener("mousemove", fnsRef.current.move);
      window.removeEventListener("mouseup", fnsRef.current.up);
      fnsRef.current = null;
    }
  }, []);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      drag.current = { startX: e.clientX, startPct: leftPercentRef.current };
      setIsDragging(true);
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";

      const move = (ev: MouseEvent) => {
        const info = drag.current;
        const container = containerRef.current;
        if (!info || !container) return;

        const w = container.clientWidth;
        if (w === 0) return;

        const deltaPct = ((ev.clientX - info.startX) / w) * 100;
        const minL = (minLeftPx / w) * 100;
        const maxL = 100 - (minRightPx / w) * 100;
        const nextPct = Math.min(Math.max(info.startPct + deltaPct, minL), maxL);
        if (Math.abs(nextPct - leftPercentRef.current) < 0.05) return;
        leftPercentRef.current = nextPct;
        scheduleUpdate(nextPct);
      };

      const up = () => cleanup();

      fnsRef.current = { move, up };
      window.addEventListener("mousemove", move);
      window.addEventListener("mouseup", up);
    },
    [containerRef, minLeftPx, minRightPx, cleanup, scheduleUpdate],
  );

  const resetRatio = useCallback(() => {
    setLeftPercent(initialPercent);
  }, [initialPercent]);

  return { leftPercent, isDragging, handleMouseDown, resetRatio };
}
