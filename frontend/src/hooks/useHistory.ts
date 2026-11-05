// Local history of questions and answers (this browser only).

import { useCallback } from "react";
import type { ResponseOut } from "../api/types";
import { useLocalStorage } from "./useLocalStorage";

const MAX_ENTRIES = 50;

export interface HistoryEntry {
  id: string;
  prompt: string;
  response: string;
  tokens: number | null;
  elapsedTime: number | null;
  failed: boolean;
  date: string; // ISO date
}

export function useHistory() {
  const [entries, setEntries] = useLocalStorage<HistoryEntry[]>("history", []);

  const add = useCallback(
    (prompt: string, result: ResponseOut) => {
      const entry: HistoryEntry = {
        id: result.request_id,
        prompt,
        response: result.response ?? result.error ?? "",
        tokens: result.tokens,
        elapsedTime: result.elapsed_time,
        failed: result.status === "failed",
        date: new Date().toISOString(),
      };
      setEntries((old) => [entry, ...old].slice(0, MAX_ENTRIES));
    },
    [setEntries],
  );

  const clear = useCallback(() => setEntries([]), [setEntries]);

  return { entries, add, clear };
}
