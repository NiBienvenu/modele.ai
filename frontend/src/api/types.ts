// JSON shapes of the REST API. Must match api/schemas.py in the backend.

export type JobStatus = "pending" | "processing" | "completed" | "failed";
export type Role = "user" | "assistant";

/** Answer of POST /question */
export interface QuestionAccepted {
  request_id: string;
  status: JobStatus;
  conversation_id: string;
}

/** Answer of GET /response/{request_id} */
export interface ResponseOut {
  request_id: string;
  status: JobStatus;
  conversation_id: string | null;
  response: string | null;
  tokens: number | null;
  elapsed_time: number | null;
  error: string | null;
}

/** One line of GET /conversations */
export interface ConversationSummary {
  id: string;
  title: string;
  updated_at: number; // Unix time in seconds
}

export interface MessageOut {
  id: string;
  role: Role;
  content: string;
  created_at: number;
  tokens: number | null;
  elapsed_time: number | null;
  failed: boolean;
}

/** Answer of GET /conversations/{id} */
export interface ConversationOut extends ConversationSummary {
  messages: MessageOut[];
}

export const isFinished = (status: JobStatus): boolean => status === "completed" || status === "failed";
