// HTTP client: the only file that talks to the backend.
// Every call sends the device id, which owns the conversations.

import { getDeviceId } from "../lib/deviceId";
import type { ConversationOut, ConversationSummary, QuestionAccepted, ResponseOut } from "./types";

// Empty = same origin (the backend serves the interface, or the Vite proxy in dev)
const API_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

/** Error with a message readable by the user. */
export class ApiError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("X-Device-Id", getDeviceId());
  if (init.body) headers.set("Content-Type", "application/json");

  let reply: Response;
  try {
    reply = await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError("Impossible de joindre le serveur. Vérifiez qu'il est lancé.");
  }
  if (!reply.ok) throw new ApiError(await readErrorMessage(reply), reply.status);
  return (reply.status === 204 ? undefined : await reply.json()) as T;
}

/** FastAPI sends errors as {"detail": "..."} or {"detail": [{msg: ...}]} */
async function readErrorMessage(reply: Response): Promise<string> {
  try {
    const body = await reply.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return body.detail.map((d: { msg: string }) => d.msg).join(", ");
  } catch {
    // Body is not JSON
  }
  return `Erreur du serveur (${reply.status})`;
}

/** POST /question */
export const sendQuestion = (prompt: string, conversationId: string | null) =>
  request<QuestionAccepted>("/question", {
    method: "POST",
    body: JSON.stringify({ prompt, conversation_id: conversationId }),
  });

/** GET /response/{request_id} */
export const fetchResponse = (requestId: string) =>
  request<ResponseOut>(`/response/${encodeURIComponent(requestId)}`);

/** GET /conversations */
export const fetchConversations = () => request<ConversationSummary[]>("/conversations");

/** GET /conversations/{id} */
export const fetchConversation = (id: string) =>
  request<ConversationOut>(`/conversations/${encodeURIComponent(id)}`);

/** DELETE /conversations/{id} */
export const deleteConversation = (id: string) =>
  request<void>(`/conversations/${encodeURIComponent(id)}`, { method: "DELETE" });
