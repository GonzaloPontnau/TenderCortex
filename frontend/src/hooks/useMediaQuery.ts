import { useSyncExternalStore } from "react";

export function useMediaQuery(query: string): boolean {
  const subscribe = (cb: () => void) => {
    const mql = window.matchMedia(query);
    mql.addEventListener("change", cb);
    return () => mql.removeEventListener("change", cb);
  };
  const getSnapshot = () => window.matchMedia(query).matches;

  return useSyncExternalStore(subscribe, getSnapshot);
}
