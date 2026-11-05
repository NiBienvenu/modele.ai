// The open conversation: its messages, sending a question, waiting for the answer.
// UI state only: the backend stores the conversation and runs the model.

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, fetchConversation, fetchResponse, sendQuestion } from "../api/client";
import { isFinished, type MessageOut, type ResponseOut } from "../api/types";
import { readStored, writeStored } from "../lib/storage";

const POLL_INTERVAL_MS = 1000;
const ACTIVE_KEY = "active-conversation";

/** A message on screen. `pending` = the answer is being generated. */
export interface ChatMessage extends MessageOut {
  pending?: boolean;
}

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
const now = () => Date.now() / 1000;
const errorText = (err: unknown) => (err instanceof ApiError ? err.message : "Erreur inattendue.");

function localMessage(role: ChatMessage["role"], content: string, extra: Partial<ChatMessage> = {}): ChatMessage {
  return {
    id: `local-${Math.random().toString(36).slice(2)}`,
    role,
    content,
    created_at: now(),
    tokens: null,
    elapsed_time: null,
    failed: false,
    ...extra,
  };
}

function answerFromResponse(result: ResponseOut, id: string): ChatMessage {
  const failed = result.status === "failed";
  return localMessage("assistant", failed ? result.error ?? "Erreur" : result.response ?? "", {
    id,
    failed,
    tokens: result.tokens,
    elapsed_time: result.elapsed_time,
  });
}

export function useChat(onConversationChanged: () => void) {
  const [activeId, setActiveId] = useState<string | null>(() => readStored(ACTIVE_KEY));
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  // Changes each time the user opens another conversation: stops old polling loops
  const sessionRef = useRef(0);

  useEffect(() => writeStored(ACTIVE_KEY, activeId), [activeId]);

  const open = useCallback(async (id: string | null) => {
    sessionRef.current += 1;
    setActiveId(id);
    setSending(false);
    setLoadError(null);
    if (id === null) {
      setMessages([]);
      return;
    }
    try {
      const conversation = await fetchConversation(id);
      setMessages(conversation.messages);
    } catch (err) {
      setMessages([]);
      if (err instanceof ApiError && err.status === 404) setActiveId(null); // Deleted elsewhere
      else setLoadError(errorText(err));
    }
  }, []);

  // Reopen the last conversation after a page reload
  useEffect(() => {
    if (activeId) void open(activeId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const replacePending = (pendingId: string, message: ChatMessage) =>
    setMessages((list) => list.map((m) => (m.id === pendingId ? message : m)));

  const send = useCallback(
    async (prompt: string) => {
      const session = sessionRef.current;
      const pending = localMessage("assistant", "", { pending: true });
      setMessages((list) => [...list, localMessage("user", prompt), pending]);
      setSending(true);
      try {
        const accepted = await sendQuestion(prompt, activeId);
        if (session !== sessionRef.current) return;
        setActiveId(accepted.conversation_id);
        onConversationChanged(); // New conversation or new order in the sidebar
        while (session === sessionRef.current) {
          const result = await fetchResponse(accepted.request_id);
          if (isFinished(result.status)) {
            if (session === sessionRef.current) replacePending(pending.id, answerFromResponse(result, pending.id));
            break;
          }
          await wait(POLL_INTERVAL_MS);
        }
      } catch (err) {
        if (session === sessionRef.current) {
          replacePending(pending.id, localMessage("assistant", errorText(err), { id: pending.id, failed: true }));
        }
      } finally {
        if (session === sessionRef.current) setSending(false);
      }
    },
    [activeId, onConversationChanged],
  );

  return { activeId, messages, sending, loadError, open, send };
}
