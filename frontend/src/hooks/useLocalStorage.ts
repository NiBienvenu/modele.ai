// State saved in the browser (localStorage).
// Storage can be blocked (private mode...), so every access is protected
// and the app still works, just without memory.

import { useEffect, useState } from "react";

function readStored<T>(key: string, fallback: T): T {
  try {
    const raw = window.localStorage.getItem(key);
    return raw === null ? fallback : (JSON.parse(raw) as T);
  } catch {
    return fallback;
  }
}

export function useLocalStorage<T>(key: string, fallback: T) {
  const [value, setValue] = useState<T>(() => readStored(key, fallback));

  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // Storage full or blocked: keep the value in memory only
    }
  }, [key, value]);

  return [value, setValue] as const;
}
