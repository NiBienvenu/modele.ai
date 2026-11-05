// List of the conversations of this device (sidebar).

import { useCallback, useEffect, useState } from "react";
import { deleteConversation, fetchConversations } from "../api/client";
import type { ConversationSummary } from "../api/types";

export function useConversations() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setConversations(await fetchConversations());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inattendue.");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const remove = useCallback(async (id: string) => {
    await deleteConversation(id);
    setConversations((list) => list.filter((c) => c.id !== id));
  }, []);

  return { conversations, error, refresh, remove };
}
