// Sends a question, then asks the backend every second until the answer is ready.
// UI state only: all the real work happens in the backend.

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, fetchResponse, sendQuestion } from "../api/client";
import { isFinished, type ResponseOut } from "../api/types";

const POLL_INTERVAL_MS = 1000;

export interface QuestionState {
  loading: boolean;
  result: ResponseOut | null;
  error: string | null;
}

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function useQuestion(onFinished: (prompt: string, result: ResponseOut) => void) {
  const [state, setState] = useState<QuestionState>({ loading: false, result: null, error: null });
  const abortRef = useRef<AbortController | null>(null);

  // Stop polling if the component disappears
  useEffect(() => () => abortRef.current?.abort(), []);

  const pollUntilFinished = useCallback(async (requestId: string, signal: AbortSignal) => {
    while (!signal.aborted) {
      const result = await fetchResponse(requestId, signal);
      setState((s) => ({ ...s, result }));
      if (isFinished(result.status)) return result;
      await wait(POLL_INTERVAL_MS);
    }
    return null;
  }, []);

  const ask = useCallback(
    async (prompt: string) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setState({ loading: true, result: null, error: null });
      try {
        const { request_id } = await sendQuestion(prompt);
        const result = await pollUntilFinished(request_id, controller.signal);
        if (result) onFinished(prompt, result);
        setState((s) => ({ ...s, loading: false }));
      } catch (err) {
        if (controller.signal.aborted) return;
        const message = err instanceof ApiError ? err.message : "Erreur inattendue.";
        setState({ loading: false, result: null, error: message });
      }
    },
    [onFinished, pollUntilFinished],
  );

  return { ...state, ask };
}
