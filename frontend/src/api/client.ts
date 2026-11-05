// HTTP client: the only file that talks to the backend.
// It knows the two endpoints and nothing else.

import type { QuestionAccepted, ResponseOut } from "./types";

// Empty = same origin (Vite proxy in dev, nginx in Docker)
const API_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

/** Error with a message readable by the user. */
export class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let reply: Response;
  try {
    reply = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new ApiError("Impossible de joindre le serveur. Vérifiez que le backend est lancé.");
  }
  if (!reply.ok) {
    throw new ApiError(await readErrorMessage(reply));
  }
  return (await reply.json()) as T;
}

/** FastAPI sends errors as {"detail": "..."} or {"detail": [{msg: ...}]} */
async function readErrorMessage(reply: Response): Promise<string> {
  try {
    const body = await reply.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return body.detail.map((d: { msg: string }) => d.msg).join(", ");
  } catch {
    // Body is not JSON: fall through
  }
  return `Erreur du serveur (${reply.status})`;
}

/** POST /question */
export function sendQuestion(prompt: string): Promise<QuestionAccepted> {
  return request<QuestionAccepted>("/question", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
}

/** GET /response/{request_id} */
export function fetchResponse(requestId: string, signal?: AbortSignal): Promise<ResponseOut> {
  return request<ResponseOut>(`/response/${encodeURIComponent(requestId)}`, { signal });
}
